#!/usr/bin/env python3
"""Timetable versions stored as patches: the shared format.

The city republishes its timetable almost daily, 41 versions in 49 days, and each
version is about 3.4 MB compressed. Stored whole, they were the largest single cost
in the repository. Consecutive versions differ in a few thousand of about 430,000
stop_times rows, so a version is stored instead as the lines added and removed
since the version before it, about 2% of the size. The first version of every
calendar month is still stored whole, so no chain is longer than a month.

A patch is an xz-compressed tar holding manifest.json and one payload per changed
member of the zip:

    manifest.json        format, base version, and for every member its zip
                         metadata, size, CRC and sha256, and how it is stored:
                         "same" (identical to the base), "full" or "diff"
    full/<name>          the member's complete bytes
    diff/<name>          an RCS-format line diff against the base member

What is rebuilt exactly: every file inside the zip, byte for byte, checked by
sha256, and therefore the project's fingerprint of the version (names, sizes and
CRCs, as in refresh_gtfs.py). What is not: the zip container. The city's zips are
compressed with a deflate encoder that zlib does not reproduce, so a rebuilt zip
has identical contents but different compressed bytes and a different file hash.

Needs only the Python standard library. Used by gtfs_pub.py (on the box, writing)
and gtfs_rebuild.py (anywhere, reading).
"""
import base64, hashlib, io, json, lzma, tarfile, zipfile

FORMAT = "vilnius-gtfs-patch/1"
META = ("compress_type", "create_system", "create_version", "extract_version",
        "flag_bits", "external_attr", "internal_attr")


def lines(data):
    """Split on newline only, keeping it, exactly as GNU diff counts lines."""
    parts = data.split(b"\n")
    out = [p + b"\n" for p in parts[:-1]]
    if parts[-1]:
        out.append(parts[-1])
    return out


def apply_rcs(old, script):
    """Apply a `diff -n` (RCS format) script to the bytes `old`."""
    src = lines(old)
    cmd = lines(script)
    out, pos, i = [], 0, 0
    while i < len(cmd):
        c = cmd[i].rstrip(b"\n")
        op, rest = c[:1], c[1:].split()
        at, n = int(rest[0]), int(rest[1])
        i += 1
        if op == b"d":
            out.extend(src[pos:at - 1])
            pos = at - 1 + n
        elif op == b"a":
            out.extend(src[pos:at])
            pos = at
            out.extend(cmd[i:i + n])
            i += n
        else:
            raise ValueError("bad diff command %r" % c)
    out.extend(src[pos:])
    return b"".join(out)


def fingerprint_infos(infos):
    """refresh_gtfs.py's fingerprint: names, sizes and CRCs, sorted."""
    parts = sorted(f"{name}:{size}:{crc}" for name, size, crc in infos)
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_patch(raw):
    """-> (manifest, {payload path: bytes})"""
    t = tarfile.open(fileobj=io.BytesIO(lzma.decompress(raw)), mode="r:")
    files = {m.name: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
    man = json.loads(files.pop("manifest.json"))
    if man.get("format") != FORMAT:
        raise ValueError("unknown patch format %r" % man.get("format"))
    return man, files


def rebuild(base_zip_bytes, patch_raw):
    """Rebuild a version from the full bytes of its base and its patch.
    Returns (zip bytes, manifest). Raises if any member fails its sha256."""
    man, files = read_patch(patch_raw)
    base = zipfile.ZipFile(io.BytesIO(base_zip_bytes))
    names = set(base.namelist())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as w:
        for m in man["members"]:
            if m["store"] == "same":
                data = base.read(m["name"])
            elif m["store"] == "full":
                data = files["full/" + m["name"]]
            elif m["store"] == "diff":
                if m["name"] not in names:
                    raise ValueError("diff against a member the base lacks: " + m["name"])
                data = apply_rcs(base.read(m["name"]), files["diff/" + m["name"]])
            else:
                raise ValueError("bad store %r" % m["store"])
            if sha(data) != m["sha256"] or len(data) != m["size"]:
                raise ValueError("member %s does not match its recorded sha256" % m["name"])
            zi = zipfile.ZipInfo(m["name"], tuple(m["date_time"]))
            for a in META:
                setattr(zi, a, m[a])
            zi.extra = base64.b64decode(m["extra"])
            zi.comment = base64.b64decode(m["comment"])
            w.writestr(zi, data, compress_type=m["compress_type"])
        w.comment = base64.b64decode(man.get("zip_comment", ""))
    out = buf.getvalue()
    z = zipfile.ZipFile(io.BytesIO(out))
    fp = fingerprint_infos((i.filename, i.file_size, i.CRC) for i in z.infolist())
    if fp != man["fingerprint"]:
        raise ValueError("rebuilt fingerprint %s, expected %s" % (fp, man["fingerprint"]))
    return out, man
