# HALO Motorworks — where we stopped

**Current version: GARAGE** (servicing and repairs). The earlier tuning version is saved as git tag `tuning-v1`.

## Garage version, Higgsfield job IDs
| What | Job ID |
|---|---|
| Garage master (car in bay, door open, rain) | 9f6e2c01-8219-44ef-9ff1-546a2a7edcf2 |
| Garage hero (empty, shutter closed) | 52867fac-93fd-46e8-b9a8-935e20d72272 |
| Brakes worn | 3c292380-e91e-4120-b55a-26cd7826d5f9 |
| Brakes new | fcd25b30-14cb-465d-81d6-8592509ac984 |
| Engine bay grimy | 8764959c-2abf-42f1-b4cb-b17c59f8f0c2 |
| Engine bay serviced | dee60ba1-fecb-42e4-996c-8faca3d95e29 |
| Sunrise, car facing out | 7c79937e-2b05-4b83-a851-448858318b0c |
| Clip: drive in (Kling 3.0 pro 7 s) | ec8eacb5-f7aa-4bd1-87b7-75bd3b69a562 (4K: 33a7ec0d-860e-411e-9195-4184ab5aec3c) |
| Clip: drive out (Kling 3.0 pro 5 s) | 32fe01f7-377d-481e-bae1-b3d608265cdc (4K: abc5089c-70ed-4849-b43a-f684b1db6fc1) |
| Not used (lift moved to the middle) | 121a0d6d-97f2-441a-a54a-83f89d0100e2 |

## Tuning version (tag tuning-v1)

**Status:** the computer version is done (preview: https://claude.ai/artifact/M78bvAMRpYstSfKdz5G2cj).
**Next:** the phone version, waiting on credits (~47 needed).

## Higgsfield job IDs: reuse these as references so everything stays identical
| What | Job ID |
|---|---|
| Master: GT-R inside, door open (chosen) | 1921496b-f31b-4406-bf27-d3c9dc116a99 |
| Master alt (not used) | ca83b26f-5ca7-4d7b-85fc-acfe704ed6ce |
| Hero: empty studio, shutter closed | 181c3e1c-2ff9-4738-80e9-1ef2fd927d40 |
| Wheel stock | b0a154ce-52ae-499a-af6e-7d0a77f7c837 |
| Wheel upgraded (forged + cyan) | bc293b6f-03df-464f-9244-610848fa056c |
| Exhaust stock | 50521733-1295-400c-9f3b-2f41b7510d4d |
| Exhaust titanium | c3a5e9e1-e9d6-4b59-8fb2-b27bcc8979bb |
| Dyno still | 2e43147f-995a-40d8-b958-516cff4a79b7 |
| Night street still | 7a7189d0-357b-46e9-a4f8-fd1950d28367 |
| Clip A: shutter + drive in (Kling 3.0 pro, 7 s, start hero / end master) | 69b9308c-4332-456c-8bfe-7906dea0d11b |
| Clip B: dyno run (Kling 3.0 pro, 5 s) | 63ea8605-9270-432e-b40c-b4d427ea0f0a |
| Clip C: night launch (Kling 3.0 pro, 5 s) | f7a09d7a-cfa7-4ca2-b4f1-f109517f8ace |

## Phone plan (9:16)
1. Phone hero (empty, shutter closed) and phone master (car inside, door open): edits referencing the hero and master above (2 × 4.25)
2. Phone dyno and phone night: reference the dyno and night stills (2 × 4.25)
3. Clip A phone: start = phone hero, end = phone master (12.25). Clips B and C phone: start = the phone stills (2 × 8.75)
4. Wheel and exhaust close-ups crop fine on phone. Only the focus points need setting.
5. Engine: load `frames/m/{a,b,c}` when `innerWidth/innerHeight < .9`, same as the Lacquer site.

## Files
- `index.html`: the whole site (canvas scroll engine, build sheet, dyno graph, configurator)
- `assets/`: stills (2560 px)
- `frames/a|b|c`: clip frames, 12 fps WebP
- `source/`: full-size originals (4K JPG) and the original clips
- `BRIEF.md`: the creative brief
