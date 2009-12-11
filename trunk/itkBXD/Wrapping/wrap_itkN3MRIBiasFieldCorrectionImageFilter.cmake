WRAP_CLASS("itk::N3MRIBiasFieldCorrectionImageFilter" POINTER)
  UNIQUE(masktype "UC")
  WRAP_IMAGE_FILTER_COMBINATIONS("${WRAP_ITK_SCALAR}" "${masktype}")
END_WRAP_CLASS()
  
