# Gaussian Attribute Extraction Notes: flight

```json
{
  "scene": "flight",
  "checkpoint": "outputs/flight/splatfacto/2024-09-12_172434/config.yml",
  "gaussian_count": 281756,
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
    "full_csv": "work/risk_aware_cbf/results/flight_gaussian_attributes.csv",
    "sample_csv": "work/risk_aware_cbf/results/flight_gaussian_attributes_sample.csv",
    "summary_csv": "work/risk_aware_cbf/results/flight_gaussian_attribute_summary.csv",
    "histograms": "work/risk_aware_cbf/figures/flight_gaussian_attribute_histograms.png"
  }
}
```

All attributes were extracted from the official `GSplatLoader` without modifying SAFER-Splat source code.
`volume_proxy` is a scale-product proxy, not a physical occupancy volume guarantee.
