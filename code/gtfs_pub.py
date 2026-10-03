#!/usr/bin/env python3
"""Publish the timetable versions the box holds, as patches where that is safe.

Run by publish.sh in place of copying every gtfs*.zip into the repository.

    python3 gtfs_pub.py pub/gtfs            # write what is missing
    python3 gtfs_pub.py pub/gtfs --dry      # say what it would write

The box keeps every version whole, as before; only what goes into the repository
changes. For each version not yet published, in the order the versions were
downloaded:

  stored whole, as gtfs-YYYYMMDD.zip, when it is the first version of its calendar
  month, when its exact bytes are already in the repository (so the copy costs
  nothing), or when a patch would not be at least five times smaller;

  otherwise stored as gtfs-YYYYMMDD.patch.xz against the version before it, but only
  after the patch has been applied to that version and every rebuilt member
  compared, by sha256, with the real one. Any mismatch and the version is stored
  whole instead.

Nothing already published is rewritten. The current feed, gtfs.zip on the box, is
published under the name refresh_gtfs.py will give it when it is replaced, so it
never has to be stored twice. The old pub/gtfs/gtfs.zip, which duplicated that
version under a second name, is removed from the working tree; git keeps it.

Format and reader: gtfs_patch.py. Rebuilding: gtfs_rebuild.py.
"""
import base64, glob, hashlib, io, json, lzma, os, re, shutil, subprocess, sys, tarfile
import tempfile, time, zipfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gtfs_patch as gp

NAME = re.compile(r"^gtfs-(\d{8})(?:-(\d+))?\.zip$")
MIN_GAIN = 5          # a patch must be at least five times smaller than the zip
DRY = "--dry" in sys.argv


def log(m):
    print(f"gtfs_pub: {m}", flush=True)


def key(name):
    m = NAME.match(name)
    return (m.group(1), int(m.group(2) or 0))


def current_name():
    """The name refresh_gtfs.py will archive gtfs.zip under: the UTC date of its
    mtime, with -1, -2 ... if that name is taken. Same rule, same answer."""
    cur = os.path.join(HERE, "gtfs.zip")
    if not os.path.exists(cur):
        return None
    d = datetime.fromtimestamp(os.stat(cur).st_mtime, timezone.utc).strftime("%Y%m%d")
    name, n = f"gtfs-{d}.zip", 1
    while os.path.exists(os.path.join(HERE, name)):
        name = f"gtfs-{d}-{n}.zip"
        n += 1
    return name


def versions():
    """[(published name, path on the box)] in download order."""
    v = [(os.path.basename(p), p) for p in glob.glob(os.path.join(HERE, "gtfs-*.zip"))
         if NAME.match(os.path.basename(p))]
    c = current_name()
    if c:
        v.append((c, os.path.join(HERE, "gtfs.zip")))
    return sorted(v, key=lambda t: key(t[0]))


def published(pub, name):
    stem = name[:-4]
    return (os.path.exists(os.path.join(pub, name))
            or os.path.exists(os.path.join(pub, stem + ".patch.xz")))


def file_sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rcs_diff(old, new):
    """GNU diff in RCS format, the cheapest exact line diff on a 1 GB machine."""
    with tempfile.TemporaryDirectory(dir=HERE, prefix=".gtfsdiff-") as t:
        a, b = os.path.join(t, "a"), os.path.join(t, "b")
        open(a, "wb").write(old)
        open(b, "wb").write(new)
        r = subprocess.run(["diff", "-n", "--binary", a, b], capture_output=True,
                           env=dict(os.environ, LC_ALL="C"))
        if r.returncode not in (0, 1):
            raise RuntimeError("diff failed: " + r.stderr.decode()[-300:])
        return r.stdout


def make_patch(base_path, base_name, new_path):
    base = zipfile.ZipFile(base_path)
    new = zipfile.ZipFile(new_path)
    bnames = set(base.namelist())
    members, payload = [], {}
    for i in new.infolist():
        data = new.read(i)
        m = {"name": i.filename, "date_time": list(i.date_time), "size": len(data),
             "crc": i.CRC, "sha256": gp.sha(data),
             "extra": base64.b64encode(i.extra).decode(),
             "comment": base64.b64encode(i.comment).decode()}
        for a in gp.META:
            m[a] = getattr(i, a)
        if i.filename in bnames:
            old = base.read(i.filename)
            if old == data:
                m["store"] = "same"
            else:
                d = rcs_diff(old, data)
                # verify the diff reproduces the member before trusting it
                if len(d) < len(data) // 2 and gp.apply_rcs(old, d) == data:
                    m["store"] = "diff"
                    payload["diff/" + i.filename] = d
                else:
                    m["store"] = "full"
                    payload["full/" + i.filename] = data
        else:
            m["store"] = "full"
            payload["full/" + i.filename] = data
        members.append(m)
    man = {"format": gp.FORMAT, "base": base_name,
           "fingerprint": gp.fingerprint_infos((i.filename, i.file_size, i.CRC)
                                               for i in new.infolist()),
           "zip_comment": base64.b64encode(new.comment).decode(),
           "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "members": members}
    tbuf = io.BytesIO()
    with tarfile.open(fileobj=tbuf, mode="w:", format=tarfile.PAX_FORMAT) as t:
        for path, data in [("manifest.json", json.dumps(man, indent=1).encode())] + sorted(payload.items()):
            ti = tarfile.TarInfo(path)
            ti.size, ti.mtime, ti.mode = len(data), 0, 0o644
            t.addfile(ti, io.BytesIO(data))
    return lzma.compress(tbuf.getvalue(), preset=6), man


def main():
    pub = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") \
        else os.path.join(HERE, "pub", "gtfs")
    os.makedirs(pub, exist_ok=True)
    vs = versions()
    have, wrote = None, 0
    for k, (name, path) in enumerate(vs):
        if published(pub, name):
            continue
        if have is None:     # hashed only on nights with something to publish
            have = {file_sha(p) for p in glob.glob(os.path.join(pub, "*.zip"))}
        prev = vs[k - 1] if k else None
        size = os.path.getsize(path)
        why = None
        if file_sha(path) in have:
            why = "its bytes are already in the repository"
        elif prev is None:
            why = "it is the first version"
        elif key(prev[0])[0][:6] != key(name)[0][:6]:
            why = "it is the first version of its month"
        if why is None:
            t0 = time.time()
            raw, man = make_patch(prev[1], prev[0], path)
            # the check that matters: rebuild from the base and compare every member
            try:
                gp.rebuild(open(prev[1], "rb").read(), raw)
                ok = True
            except Exception as e:
                log(f"{name}: patch failed its rebuild check ({e}), storing whole")
                ok = False
            if ok and len(raw) * MIN_GAIN <= size:
                stores = {}
                for m in man["members"]:
                    stores[m["store"]] = stores.get(m["store"], 0) + 1
                log(f"{name}: patch against {prev[0]}, {len(raw)/1024:.0f} KB instead of "
                    f"{size/1024/1024:.1f} MB, members {stores}, {time.time()-t0:.0f}s")
                if not DRY:
                    out = os.path.join(pub, name[:-4] + ".patch.xz")
                    open(out + ".part", "wb").write(raw)
                    os.replace(out + ".part", out)
                wrote += 1
                continue
            if ok:
                why = f"a patch would be {len(raw)/1024:.0f} KB, not small enough"
            else:
                why = "the patch did not rebuild exactly"
        log(f"{name}: stored whole, {why}")
        if not DRY:
            shutil.copyfile(path, os.path.join(pub, name + ".part"))
            os.replace(os.path.join(pub, name + ".part"), os.path.join(pub, name))
            have.add(file_sha(path))
        wrote += 1
    old = os.path.join(pub, "gtfs.zip")
    if os.path.exists(old):
        cur = current_name()
        if (cur and published(pub, cur)) or DRY:
            log("removing pub/gtfs/gtfs.zip; its version is published under its own name")
            if not DRY:
                os.unlink(old)
    log(f"{len(vs)} versions held, {wrote} written this run")


if __name__ == "__main__":
    main()
