/*=========================================================================

  Program:   BioImageXD
  Module:    itkDynamicThreshold3DImageFilter.txx
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

#ifndef __itkDynamicThreshold3DImageFilter_txx
#define __itkDynamicThreshold3DImageFilter_txx

#include "itkDynamicThreshold3DImageFilter.h"
#include "itkProgressReporter.h"
#include "itkMeanImageFilter.h"
#include "itkMedianImageFilter.h"
#include "itkImageRegionConstIterator.h"
#include "itkImageRegionIterator.h"
#include "itkProgressAccumulator.h"
#include "itkProgressReporter.h"

namespace itk {

template<class TInputImage, class TOutputImage>
DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::DynamicThreshold3DImageFilter()
{
  this->SetNumberOfRequiredInputs(1);
  this->m_StatisticsType = 0;
  this->m_UseImageSpacing = 1;
  unsigned int defaultRad = 2;
  if (ImageDimension == 2)
	{
	  this->SetRadius(defaultRad,defaultRad);
	}
  else
	{
	  this->SetRadius(defaultRad,defaultRad,defaultRad);
	}
  this->m_InsideValue = vcl_numeric_limits<OutputPixelType>::max();
  this->m_OutsideValue = 0;
  this->m_Threshold = 0;
}

template<class TInputImage, class TOutputImage>
DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::~DynamicThreshold3DImageFilter()
{
  this->Unallocate();
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::Unallocate()
{
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::PrintSelf(std::ostream &os, Indent indent) const
{
  Superclass::PrintSelf(os,indent);
  os << indent << "Radius: (" << this->m_Radius[0] << "," << this->m_Radius[1] << "," << this->m_Radius[2] << ")" << std::endl;
  if (this->m_StatisticsType == itkGetStaticConstMacro(Mean))
	{
	  os << indent << "Statistics type: Mean" << std::endl;
	}
  else
	{
	  os << indent << "Statistics type: Median" << std::endl;
	}
  if (this->m_UseImageSpacing)
	{
	  os << indent << "Use image spacing: True" << std::endl;
	}
  else
	{
	  os << indent << "Use image spacing: False" << std::endl;
	}
  os << indent << "Inside value: " << this->m_InsideValue << std::endl;
  os << indent << "Outside value: " << this->m_OutsideValue << std::endl;
  os << indent << "Threshold: " << this->m_Threshold << std::endl;
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::GenerateData()
{
  const TInputImage* inputImage = this->GetInput();
  this->AllocateOutputImage();
  TOutputImage* outputImage = this->GetOutput();

  const typename TOutputImage::RegionType& region = outputImage->GetRequestedRegion();
  const typename TOutputImage::SpacingType& spacing = outputImage->GetSpacing();
  typedef itk::MeanImageFilter<TInputImage,TInputImage> MeanType;
  typedef itk::MedianImageFilter<TInputImage,TInputImage> MedianType;
  typedef itk::ImageRegionConstIterator<TInputImage> InputIteratorType;
  typedef itk::ImageRegionIterator<TOutputImage> OutputIteratorType;

  typename TInputImage::SizeType radius;
  if (this->m_UseImageSpacing)
	{
	  radius[0] = this->m_Radius[0];
	  if (this->m_UseImageSpacing)
		{
		  radius[1] = static_cast<InputPixelType>(round(this->m_Radius[1] * (spacing[0] / spacing[1])));
		  if (ImageDimension == 3) radius[2] = static_cast<InputPixelType>(round(this->m_Radius[2] * (spacing[0] / spacing[2])));
		}
	  else
		{
		  radius[1] = this->m_Radius[1];
		  if (ImageDimension == 3) radius[2] = this->m_Radius[2];
		}
	}

  ProgressAccumulator::Pointer pipelineProgress = ProgressAccumulator::New();
  //itk::ProgressReporter progress(this,0,region.GetNumberOfPixels(),100);
  pipelineProgress->SetMiniPipelineFilter(this);
  itkDebugMacro(<< "Using radius (" << radius[0] << "," << radius[1] << "," << radius[2] << ")");
  if (this->m_StatisticsType == Mean)
	{
	  typename MeanType::Pointer mean = MeanType::New();
	  mean->SetRadius(radius);
	  mean->SetInput(inputImage);
	  pipelineProgress->RegisterInternalFilter(mean,1.0f);
	  //pipelineProgress->RegisterInternalFilter(this,0.33f);
	  mean->GraftOutput(this->GetOutput());
	  mean->Update();
	  this->GraftOutput(mean->GetOutput());
	}
  else
	{
	  typename MedianType::Pointer median = MedianType::New();
	  median->SetRadius(radius);
	  median->SetInput(inputImage);
	  pipelineProgress->RegisterInternalFilter(median,1.0f);
	  //pipelineProgress->RegisterInternalFilter(this,0.25f);
	  median->GraftOutput(this->GetOutput());
	  median->Update();
	  this->GraftOutput(median->GetOutput());
	}

  InputIteratorType inIter(inputImage,region);
  OutputIteratorType outIter(outputImage,region);
  // Calculate dynamic threshold per pixel and set pixel values to min or max
  for (inIter.GoToBegin(), outIter.GoToBegin(); !inIter.IsAtEnd(); ++inIter, ++outIter)
	{
	  if (inIter.Get() - this->m_Threshold >= outIter.Get())
		{
		  outIter.Set(this->m_InsideValue);
		}
	  else
		{
		  outIter.Set(this->m_OutsideValue);
		}
	  //progress.CompletedPixel();
	}
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::GenerateInputRequestedRegion()
{
  Superclass::GenerateInputRequestedRegion();
  TInputImage* input = const_cast<TInputImage*>(this->GetInput());
  if (input)
	{
	  input->SetRequestedRegionToLargestPossibleRegion();
	}
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::AllocateOutputImage()
{
  const TInputImage* inputImage = this->GetInput();
  this->GetOutput()->SetRegions(inputImage->GetRequestedRegion());
  this->GetOutput()->SetSpacing(inputImage->GetSpacing());
  this->GetOutput()->SetOrigin(inputImage->GetOrigin());
  this->GetOutput()->Allocate();
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetStatisticsType(int type)
{
  if (type == this->m_StatisticsType) return;

  if (type == itkGetStaticConstMacro(Median))
	{
	  this->m_StatisticsType = type;
	}
  else
	{
	  this->m_StatisticsType = itkGetStaticConstMacro(Mean);
	}

  this->Modified();
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetStatisticsTypeMean()
{
  this->SetStatisticsType(itkGetStaticConstMacro(Mean));
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetStatisticsTypeMedian()
{
  this->SetStatisticsType(itkGetStaticConstMacro(Median));
}

template<class TInputImage, class TOutputImage>
int DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetRadius(unsigned int x, unsigned int y, unsigned int z = 0)
{
  if (x >= 0 && y >= 0 && z >= 0 && (x != this->m_Radius[0] || y != this->m_Radius[1] || z != this->m_Radius[2]))
	{
	  this->m_Radius[0] = x;
	  this->m_Radius[1] = y;
	  this->m_Radius[2] = z;
	  this->Modified();
	  return 1;
	}
  return 0;
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetUseImageSpacing(int value)
{
  if (value)
	{
	  this->SetUseImageSpacingOn();
	}
  else
	{
	  this->SetUseImageSpacingOff();
	}
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetUseImageSpacingOn()
{
  this->m_UseImageSpacing = 1;
}

template<class TInputImage, class TOutputImage>
void DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::SetUseImageSpacingOff()
{
  this->m_UseImageSpacing = 0;
}

  /*template<class TInputImage, class TOutputImage>
const typename DynamicThreshold3DImageFilter<TInputImage,TOutputImage>::NeighborhoodType&
DynamicThreshold3DImageFilter<TInputImage,TOutputImage>
::GetNeighborhood() const
{
  return this->m_Neighborhood;
  }*/

}

#endif
