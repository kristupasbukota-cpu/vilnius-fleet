# The five districts promised more frequent routes

2 October 2026. Task #7, the third of JUDU's public claims tested against the feed.

**The claim.** JUDU's announcement of 20 August 2026 said more frequent routes were
planned for densely populated residential districts "such as Fabijoniškės,
Perkūnkiemis, Baltupiai, Šiaurės miestelis, Lazdynėliai". It named no routes and
no frequencies.

**The verdict: four of five got more service than the city as a whole; Baltupiai
did not.** And in two of them the new morning is slower than before: in Lazdynėliai,
buses leaving the district between 07:00 and 09:00 now lose about 32 s more per hop
than the city's own change.

---

## 1. Where the districts are

The city's own sub-district boundaries, **"Vilniaus miesto seniūnaitijų ribos"**,
from Vilniaus planas's open data server (`zemelapiai.vplanas.lt`, Open_Data,
Vilniaus_miesto_ribos, layer 2). Fabijoniškės is the whole eldership; the other four
are the sub-districts of the same name, in Pašilaičiai, Verkiai, Žirmūnai and
Lazdynai. Stops inside each:

| district | area | stops |
|---|---|---|
| Fabijoniškės | 6.0 km² | 48 |
| Lazdynėliai | 4.1 km² | 12 |
| Šiaurės miestelis | 0.2 km² | 4 |
| Baltupiai | 0.6 km² | 3 |
| Perkūnkiemis | 0.2 km² | 2 |

The last three are small, so each depends on a handful of stops.

## 2. Service planned: timetabled calls at the district's stops

Average working day, Tuesday to Thursday of one summer week (25 to 27 August) against
one autumn week (22 to 24 September), each from the timetable version in force:

| district | summer calls a day | autumn | **change** | change 07-09 |
|---|---|---|---|---|
| Šiaurės miestelis | 1,358 | 1,666 | **+22.7%** | **+30.6%** |
| Perkūnkiemis | 368 | 450 | **+22.3%** | +16.0% |
| Lazdynėliai | 920 | 1,094 | **+18.9%** | +16.0% |
| Fabijoniškės | 7,863 | 9,176 | **+16.7%** | +7.4% |
| Baltupiai | 1,075 | 1,159 | +7.8% | +4.6% |
| **rest of the city** | 195,127 | 214,536 | **+9.9%** | **+10.5%** |

Fabijoniškės gained route 49. Baltupiai gained route 52 and lost 55; Šiaurės
miestelis lost 89 but gained calls on its other routes.

## 3. Service delivered: hops observed leaving the district's stops

Monday to Thursday, 8 summer days against 18 autumn days:

| district | change in observed hops |
|---|---|
| Perkūnkiemis | +305% |
| Lazdynėliai | +26.7% |
| Šiaurės miestelis | +20.3% |
| Fabijoniškės | +18.5% |
| Baltupiai | +7.3% |
| **rest of the city** | **+17.2%** |

Perkūnkiemis's figure rests on two stops, both mid-route, and is far larger than
its 22% rise in timetabled calls. I cannot explain the size of it from the data
here. Read it as "more", not as a number.

**The two measures disagree about the rest of the city**, +9.9% timetabled calls
against +17.2% observed hops, while the fleet grew about 17%. I have not resolved why the timetabled
count rose less than the observed one. The district comparison holds either
way: on both measures Šiaurės miestelis, Lazdynėliai and Perkūnkiemis gained more
than the city, Fabijoniškės about the same as or more than the city, and
Baltupiai less.

## 4. What happened to the morning

Mean delay per hop on links leaving the district, 07:00 to 09:00, Monday to
Thursday:

| district | summer | autumn | change | change minus the city's, 95% CI |
|---|---|---|---|---|
| **Lazdynėliai** | -5.7 s | **+34.0 s** | +39.7 | **+31.9 [+25.7, +38.4]** |
| Šiaurės miestelis | +0.5 s | +29.0 s | +28.5 | +20.7 [-3.8, +54.8] |
| Fabijoniškės | +0.6 s | +10.1 s | +9.5 | +1.8 [-0.3, +3.8] |
| Baltupiai | -0.7 s | +4.9 s | +5.6 | -2.1 [-5.0, +0.7] |
| rest of the city | +2.0 s | +9.7 s | +7.7 | |

Perkūnkiemis has no summer morning hops to compare.

**Lazdynėliai's morning got much worse, and it is two links.** From Oslo st. to
Erfurto st. a bus used to lose +6 s and now loses +55 s; from Oslo st. to Jonažolių
st., -5 s became +50 s. Both are the way out of the district towards the city, and
they fit the 2 October finding that the autumn morning problem is inbound. More buses
were added to Lazdynėliai; they now queue to get out of it.

Šiaurės miestelis points the same way but rests on 69 morning hops a day and the
interval is wide.

## Verdict

**Claim largely confirmed.** Four of the five named districts received a larger
increase in timetabled service than the rest of the city, and the delivered service
agrees. Baltupiai is the exception: its increase is below the city's on both
measures.

**What the promise did not cover is the road.** In Lazdynėliai the extra buses now
lose about half a minute per hop more than before on the way out each morning. More
frequent routes into a district only help if the buses can leave it.

## Method

Boundaries: `https://zemelapiai.vplanas.lt/arcgis/rest/services/Open_Data/Vilniaus_miesto_ribos/MapServer/2`,
geometry only. Timetabled calls: every `stop_times` row at the district's stops for
trips active on the day, from the latest version in `gtfs/` dated no later than the
day after. Observed hops and delay: `analysis/trav-*.csv.gz`, hops whose
`stop_from_id` lies in the district. The interval is a bootstrap over days for the
district and the city separately.
