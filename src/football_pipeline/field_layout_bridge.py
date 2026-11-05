"""Experimental motion eligibility for an underdetermined visible field layout."""

from .field_motion import _canonical_layout_determined, estimate_checked

LAYOUT_BRIDGE_RULE = "rank_deficient_visible_layout_motion_only_v1"


def estimate_layout_bridge(observation, image_size, settings):
    """Missing geometric information must not create a new direct homography.

    As with fewer than four visible points, a rank-deficient canonical layout
    can only be recovered by the existing checked motion path. Invalid image
    coordinates and collapsed predictions of an identifiable layout stay hard
    failures. No motion anchor is created or refreshed here.
    """
    result = estimate_checked(observation, image_size, settings)
    if (
        result["status"] == "degenerate_geometry"
        and len(result["points"]) >= 4
        and not _canonical_layout_determined(result["points"])
    ):
        result["status"] = "insufficient_fit_geometry"
        result["quality"].update(
            motion_eligibility_rule=LAYOUT_BRIDGE_RULE,
            canonical_full_layout_rank_deficient=True,
            direct_homography_created=False,
        )
    return result
