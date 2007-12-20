/*=========================================================================

  Program:   BioImageXD
  Module:    itkDynamicThresholdImageFilter.txx
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

#ifndef _itkDynamicThresholdImageFilter_txx
#define _itkDynamicThresholdImageFilter_txx

#include "itkDynamicThresholdImageFilter.h"
#include "itkProgressReporter.h"

namespace itk {

template<class TInputImage, class TOutputImage>
DynamicThresholdImageFilter<TInputImage,TOutputImage>
::DynamicThresholdImageFilter()
{
  this->SetNumberOfRequiredInputs(1);
  this->m_StatisticsType = 0;
  unsigned int defaultNbh = 5;
  this->SetNeighborhood(defaultNbh,defaultNbh);
  this->m_InsideValue = vcl_numeric_limits<OutputPixelType>::max();
  this->m_OutsideValue = 0;
}

template<class TInputImage, class TOutputImage>
DynamicThresholdImageFilter<TInputImage,TOutputImage>
::~DynamicThresholdImageFilter()
{
  this->Unallocate();
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::Unallocate()
{
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::PrintSelf(std::ostream &os, Indent indent) const
{
  Superclass::PrintSelf(os,indent);
  os << indent << "Neighborhood: (" << this->m_Neighborhood.first << "," << this->m_Neighborhood.second << ")" << std::endl;
  if (this->m_StatisticsType == itkGetStaticConstMacro(Mean))
	{
	  os << indent << "Statistics type: Mean" << std::endl;
	}
  else
	{
	  os << indent << "Statistics type: Median" << std::endl;
	}
  os << indent << "Inside value: " << this->m_InsideValue << std::endl;
  os << indent << "Outside value: " << this->m_OutsideValue << std::endl;
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::GenerateData()
{
  const TInputImage* inputImage = this->GetInput();
  this->AllocateOutputImage();
  TOutputImage* outputImage = this->GetOutput();
  unsigned int imgDim = TInputImage::GetImageDimension();
  const typename TOutputImage::RegionType& region = outputImage->GetRequestedRegion();
  const typename TOutputImage::SizeType& regionSize = region.GetSize();
  unsigned long columns = regionSize.m_Size[0];
  unsigned long rows = regionSize.m_Size[1];
  unsigned long slices;
  slices = imgDim > 2 ? regionSize.m_Size[2] : 1;

  // Create vector for column counters. Use column counter that the whole
  // neighborhood wouldn't have to be calculated every time. Only new column
  // needs to be calculated.
  std::vector<double> columnCounters(columns);
  // Create vector that contains pixels of neighborhood
  std::vector<VectorType> columnPixels(columns);
  // Create vector for median pixels
  VectorType medianPixels(this->m_Neighborhood.first * this->m_Neighborhood.second);

  long nIterCols = (this->m_Neighborhood.first - 1) / 2;
  long nIterRows = (this->m_Neighborhood.second - 1) / 2;
  unsigned long startCol;
  unsigned long endCol;
  unsigned long startRow;
  unsigned long endRow;
  unsigned long nbhSize;

  // Create iterator for input and output images
  typename TInputImage::RegionType::IndexType indexStart;
  indexStart[0] = 0;
  indexStart[1] = 0;
  typename TInputImage::RegionType::SizeType size;
  size[0] = columns;
  size[1] = rows;
  if (imgDim > 2)
	{
	  indexStart[2] = 0;
	  size[2] = slices;
	}
  typename TInputImage::RegionType outRegion;
  outRegion.SetSize(size);
  outRegion.SetIndex(indexStart);
  itk::ImageRegionConstIterator<TInputImage> inIter(inputImage,outRegion);
  itk::ImageRegionIterator<TOutputImage> outIter(outputImage,outRegion);

  // Calculate dynamic threshold per pixel and set pixel values to min or max
  long x = 0;
  long y = 0;
  long z = 0;
  itk::ProgressReporter progress(this,0,rows*columns*slices,100);
  for (z = 0; z < slices; ++z)
	{
	  for (y = 0; y < rows; ++y)
		{
		  for (x = 0; x < columns; ++x)
			{
			  if (x == 0) // New row, re-calculate whole neighborhood
				{
				  for (unsigned long nIter = 0; nIter <= nIterCols; ++nIter)
					{
					  this->GetColumnPixels(nIter,y,z,inputImage,columnPixels[nIter]);
					  columnCounters[nIter] = this->CalculateColumnSum(columnPixels[nIter]);
					}
				}
			  else
				{
				  long nextCol = x + nIterCols;
				  if (nextCol < columns)
					{
					  this->GetColumnPixels(nextCol,y,z,inputImage,columnPixels[nextCol]);
					  columnCounters[nextCol] = this->CalculateColumnSum(columnPixels[nextCol]);
					}
				}

			  // Calculate pixel threshold value
			  startCol = x - nIterCols >= 0 ? x - nIterCols : 0;
			  endCol = x + nIterCols < columns ? x + nIterCols : columns - 1;
			  startRow = y - nIterRows >= 0 ? y - nIterRows : 0;
			  endRow = y + nIterRows < rows ? y + nIterRows : rows - 1;
			  nbhSize = (endCol - startCol + 1) * (endRow - startRow + 1);
			  double threshold = 0.0;

			  if (this->m_StatisticsType == 0) // Mean
				{
				  double sum = 0.0;
				  while (startCol <= endCol)
					{
					  sum += columnCounters[startCol];
					  startCol++;
					}
				  threshold = sum / nbhSize;
				}
			  else // Median
				{
				  typename VectorType::const_iterator colIter;
				  medianPixels.clear();
				  unsigned long medianPos = nbhSize / 2;

				  while (startCol <= endCol)
					{
					  for (colIter = columnPixels[startCol].begin(); colIter != columnPixels[startCol].end(); ++colIter)
						{
						  medianPixels.push_back(*colIter);
						}
					  startCol++;
					}
				  typename std::vector<InputPixelType>::iterator medianIterator = medianPixels.begin() + medianPos;
				  std::nth_element(medianPixels.begin(),medianIterator,medianPixels.end());
				  threshold = *medianIterator;
				}

			  inIter.Get() > threshold ? outIter.Set(this->m_InsideValue) : outIter.Set(this->m_OutsideValue);
			  ++inIter;
			  ++outIter;

			  itkDebugMacro("Threshold for pixel (" << x << "," << y << "," << z << "): " << threshold);
			  progress.CompletedPixel();
			}
		}
	}
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
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
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::AllocateOutputImage()
{
  const TInputImage* inputImage = this->GetInput();
  this->GetOutput()->SetRegions(inputImage->GetRequestedRegion());
  this->GetOutput()->SetSpacing(inputImage->GetSpacing());
  this->GetOutput()->SetOrigin(inputImage->GetOrigin());
  this->GetOutput()->Allocate();
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::GetColumnPixels(unsigned long x,unsigned long y,unsigned long z,const TInputImage* image,VectorType &column) const
{
  long largestX = image->GetRequestedRegion().GetSize().m_Size[0];
  if (x > largestX) return;

  long startY = y - (this->m_Neighborhood.second - 1) / 2;
  startY = startY >= 0 ? startY : 0;
  long endY = y + (this->m_Neighborhood.second - 1) / 2;
  long largestY = image->GetRequestedRegion().GetSize().m_Size[1];
  endY = endY < largestY ? endY : largestY - 1;

  // Create image iterator
  typename TInputImage::RegionType::IndexType indexStart;
  indexStart[0] = x;
  indexStart[1] = startY;
  typename TInputImage::RegionType::SizeType size;
  size[0] = 1;
  size[1] = endY - startY + 1;
  if (TInputImage::GetImageDimension() > 2)
	{
	  indexStart[2] = z;
	  size[2] = 1;
	}
  typename TInputImage::RegionType region;
  region.SetSize(size);
  region.SetIndex(indexStart);
  itk::ImageRegionConstIterator<TInputImage> iter(image, region);

  column.clear();
  for (iter.GoToBegin(); !iter.IsAtEnd(); ++iter)
	{
	  column.push_back(iter.Get());
	}
}

template<class TInputImage, class TOutputImage>
double DynamicThresholdImageFilter<TInputImage,TOutputImage>
::CalculateColumnSum(VectorType &column) const
{
  double sum = 0.0;
  typename VectorType::const_iterator iter;
  for (iter = column.begin(); iter != column.end(); ++iter)
	{
	  sum += *(iter);
	}

  return sum;
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::SetStatisticsType(int type)
{
  if (type == itkGetStaticConstMacro(Median))
	{
	  this->m_StatisticsType = itkGetStaticConstMacro(Median);
	}
  else
	{
	  this->m_StatisticsType = itkGetStaticConstMacro(Mean);
	}
  this->Modified();
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::SetStatisticsTypeMean()
{
  this->SetStatisticsType(itkGetStaticConstMacro(Mean));
}

template<class TInputImage, class TOutputImage>
void DynamicThresholdImageFilter<TInputImage,TOutputImage>
::SetStatisticsTypeMedian()
{
  this->SetStatisticsType(itkGetStaticConstMacro(Median));
}

template<class TInputImage, class TOutputImage>
int DynamicThresholdImageFilter<TInputImage,TOutputImage>
::SetNeighborhood(unsigned int first, unsigned int second)
{
  if (first > 0 && second > 0)
	{
	  first = first % 2 ? first : first + 1;
	  second = second % 2 ? second : second + 1;
	  this->m_Neighborhood.first = first;
	  this->m_Neighborhood.second = second;
	  this->Modified();
	  return 1;
	}
  return 0;
}

template<class TInputImage, class TOutputImage>
int DynamicThresholdImageFilter<TInputImage,TOutputImage>
::SetRadius(unsigned int beside, unsigned int below)
{
  return this->SetNeighborhood(beside * 2 + 1,below * 2 + 1);
}

template<class TInputImage, class TOutputImage>
const typename DynamicThresholdImageFilter<TInputImage,TOutputImage>::NeighborhoodType&
DynamicThresholdImageFilter<TInputImage,TOutputImage>
::GetNeighborhood() const
{
  return this->m_Neighborhood;
}

}

#endif
