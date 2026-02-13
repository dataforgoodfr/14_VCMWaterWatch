Workflows that manipulate data directly in NocoDB (no staging files involved).

# calculate_distribution_zone

Computes the geometry of distribution zones that are missing one, by merging the geometries of their linked municipalities (using Shapely `unary_union`). Updates the zones in-place.

# clean_blank_actors

Deletes Actor records that have a blank (null) name.