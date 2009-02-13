/*=========================================================================

  Program:   BioImageXD
  Module:    itkDynamicThreshold3DImageFilter.h
  Language:  C++
  Date:      $Date$
  Version:   $Revision$


 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

=========================================================================*/

#ifndef __itkDynamicThreshold3DImageFilter_h
#define __itkDynamicThreshold3DImageFilter_h

#include "itkImageToImageFilter.h"

namespace itk {
/** \class DynamicThreshold3DImageFilter
 * \brief Applies dynamic thresholding to an image
 *
 * This filter computes dynamic threshold of a pixel by checking its 
 * neighborhood. Output image pixel is then given an inside or an outside 
 * value.
 *
 * Dynamic threshold of an pixel can be computed as mean or median of its
 * neighborhood pixels.
 *
 */
template<class TInputImage, class TOutputImage>
class ITK_EXPORT DynamicThreshold3DImageFilter : 
    public ImageToImageFilter<TInputImage, TOutputImage>
{
public:
  /* Default typedefs */
  typedef DynamicThreshold3DImageFilter Self;
  typedef ImageToImageFilter<TInputImage, TOutputImage> Superclass;
  typedef SmartPointer<Self> Pointer;
  typedef SmartPointer<const Self> ConstPointer;

  /* Own typedefs */
  typedef typename TInputImage::PixelType InputPixelType;
  typedef typename TOutputImage::PixelType OutputPixelType;
  typedef typename std::vector<InputPixelType> VectorType;

  /* Macros */
  itkNewMacro(Self);
  itkTypeMacro(DynamicThreshold3DImageFilter, ImageToImageFilter);
  itkStaticConstMacro(Mean, int, 0);
  itkStaticConstMacro(Median, int, 1);
  itkGetConstMacro(StatisticsType, int);
  itkSetMacro(InsideValue, OutputPixelType);
  itkGetConstMacro(InsideValue, OutputPixelType);
  itkSetMacro(OutsideValue, OutputPixelType);
  itkGetConstMacro(OutsideValue, OutputPixelType);
  itkSetMacro(Threshold, OutputPixelType);
  itkGetMacro(Threshold, OutputPixelType);
  itkStaticConstMacro(ImageDimension, unsigned int, TOutputImage::ImageDimension);
  itkGetMacro(UseImageSpacing, int);
  itkGetVectorMacro(Radius, const unsigned int, TOutputImage::ImageDimension);


  /* Public methods */
  void SetStatisticsType(int);
  void SetStatisticsTypeMean();
  void SetStatisticsTypeMedian();
  void SetUseImageSpacing(int);
  void SetUseImageSpacingOn();
  void SetUseImageSpacingOff();
  int SetRadius(unsigned int, unsigned int, unsigned int);

protected:
  DynamicThreshold3DImageFilter();
  ~DynamicThreshold3DImageFilter();
  void Unallocate();
  void PrintSelf(std::ostream&, Indent) const;
  void GenerateData();
  void GenerateInputRequestedRegion();
  void AllocateOutputImage();

private:
  DynamicThreshold3DImageFilter(const Self&); // purposely not implemented
  void operator=(const Self&); // purposely not implemented

  int m_StatisticsType; // 0 = mean, 1 = median
  int m_UseImageSpacing;
  unsigned int m_Radius[3];
  OutputPixelType m_InsideValue;
  OutputPixelType m_OutsideValue;
  OutputPixelType m_Threshold;
};
}

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkDynamicThreshold3DImageFilter.txx"
#endif

#endif
