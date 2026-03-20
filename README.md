# fantasy-analytics-engine
I want to build my own program where I can take in data from MLB, synthesize it, then use it to assist me in playing fantasy baseball. I want to be able to track specific stats for players to help me get an edge in drafting, finding gems in the rough through waivers throughout the season, and get weekly reports when the current season is on-going.


## V1 implementation planning

- Detailed V1 vertical slice module layout and function signatures: `docs/v1_slice_module_plan.md`

## Current scaffold status

- Created the V1 package/module layout from `docs/v1_slice_module_plan.md`.
- Implemented `fantasy_analytics_engine/domain/models.py`.
- Implemented `fantasy_analytics_engine/config.py`.
- Added ingestion note for planned `MLB-StatsAPI` usage.

## 2024 season backfill script

A concrete ingestion backfill script is available at:
`fantasy_analytics_engine/ingestion/backfill_2024_season.py`

It processes **2024-03-20** through **2024-09-30** with a daily schedule loop, game-level boxscore ingestion, player upserts, batting/pitching stat upserts, fantasy point computation, batch commits every 5 days, and API pacing.
