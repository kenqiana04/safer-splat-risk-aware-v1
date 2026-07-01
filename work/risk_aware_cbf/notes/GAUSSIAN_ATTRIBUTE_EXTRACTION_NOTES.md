# Gaussian Attribute Extraction Notes

```json
{
  "checkpoint": "outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml",
  "gaussian_count": 116446,
  "device": "cuda",
  "available_attributes": [
    "means",
    "scales",
    "max/min/mean scale",
    "anisotropy",
    "volume_proxy",
    "distance_to_scene_center",
    "opacity",
    "rotation/quaternion",
    "color_or_sh_norm"
  ],
  "missing_attributes": [],
  "outputs": {
    "full_csv": "work/risk_aware_cbf/results/stonehenge_gaussian_attributes.csv",
    "sample_csv": "work/risk_aware_cbf/results/stonehenge_gaussian_attributes_sample.csv",
    "summary_csv": "work/risk_aware_cbf/results/stonehenge_gaussian_attribute_summary.csv",
    "histograms": "work/risk_aware_cbf/figures/stonehenge_gaussian_attribute_histograms.png"
  }
}
```

All attributes were extracted from the official `GSplatLoader` without modifying SAFER-Splat source code.
`volume_proxy` is a scale-product proxy, not a physical occupancy volume guarantee.
