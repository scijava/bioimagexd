/*=========================================================================

Program:   Insight Segmentation & Registration Toolkit
Module:    $RCSfile: itkLabelShapeImageFilter.txx,v $
Language:  C++
Date:      $Date: 2005/05/14 12:55:47 $
Version:   $Revision: 1.11 $

Copyright (c) Insight Software Consortium. All rights reserved.
See ITKCopyright.txt or http://www.itk.org/HTML/Copyright.htm for details.

This software is distributed WITHOUT ANY WARRANTY; without even 
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#ifndef _itkLabelShapeImageFilter_txx
#define _itkLabelShapeImageFilter_txx
#include "itkLabelShapeImageFilter.h"

#include "itkImageRegionIterator.h"
#include "itkImageRegionConstIteratorWithIndex.h"
#include "itkNumericTraits.h"
#include "itkProgressReporter.h"

namespace itk {

template<class ImageType>
LabelShapeImageFilter<ImageType>
::LabelShapeImageFilter()
{
  this->SetNumberOfRequiredInputs(1);
}



template<class ImageType>
void
LabelShapeImageFilter<ImageType>
::GenerateInputRequestedRegion()
{
  Superclass::GenerateInputRequestedRegion();
  if ( this->GetInput() )
    {
    ImagePointer image =
      const_cast< typename Superclass::InputImageType * >( this->GetInput() );
    image->SetRequestedRegionToLargestPossibleRegion();
    }
}

template<class ImageType>
void
LabelShapeImageFilter<ImageType>
::EnlargeOutputRequestedRegion(DataObject *data)
{
  Superclass::EnlargeOutputRequestedRegion(data);
  data->SetRequestedRegionToLargestPossibleRegion();
}


template<class ImageType>
void
LabelShapeImageFilter<ImageType>
::AllocateOutputs()
{
  // Pass the input through as the output
  ImagePointer image = const_cast< ImageType * >( this->GetInput() );
  this->GraftOutput( image );

  // Nothing that needs to be allocated for the remaining outputs
}

template<class ImageType>
void
LabelShapeImageFilter<ImageType>
::BeforeThreadedGenerateData()
{
  int numberOfThreads = this->GetNumberOfThreads();

  // Resize the thread temporaries
  m_LabelShapePerThread.resize(numberOfThreads);
  
  // Initialize the temporaries
  for (int i=0; i < numberOfThreads; ++i)
    {
    m_LabelShapePerThread[i].clear();
    }

  // Initialize the final map
  m_LabelShape.clear();
  m_Labels.clear();
}

template<class ImageType>
void
LabelShapeImageFilter<ImageType>
::AfterThreadedGenerateData()
{
  MapIterator mapIt;
  MapConstIterator threadIt;
  int i;
  int numberOfThreads = this->GetNumberOfThreads();

  // Run through the map for each thread and accumulate the count,
  // sum, and sumofsquares
  for (i = 0; i < numberOfThreads; i++)
    {
    // iterate over the map for this thread
    for (threadIt = m_LabelShapePerThread[i].begin();
      threadIt != m_LabelShapePerThread[i].end();
      ++threadIt)
      {
      // does this label exist in the cumulative stucture yet?
      mapIt = m_LabelShape.find( (*threadIt).first );
      if (mapIt == m_LabelShape.end())
        {
        // create a new entry
        typedef typename MapType::value_type MapValueType;
        mapIt = m_LabelShape.insert( MapValueType((*threadIt).first,  LabelShape()) ).first;
        for (int i=0; i<ImageDimension; i++)
          {
          (*mapIt).second.m_BoundingBox.SetIndex(i, (*threadIt).second.m_BoundingBox.GetIndex(i));
          (*mapIt).second.m_BoundingBox.SetSize(i, (*threadIt).second.m_BoundingBox.GetSize(i));
          }
        }

      // accumulate the information from this thread
      (*mapIt).second.m_Volume += (*threadIt).second.m_Volume;
      
      const CenterOfGravityType * tcog = &(*threadIt).second.m_CenterOfGravity;
      const BoundingBoxType * tbb = &(*threadIt).second.m_BoundingBox;
      CenterOfGravityType * cog = &(*mapIt).second.m_CenterOfGravity;
      BoundingBoxType * bb = &(*mapIt).second.m_BoundingBox;
      
      for (int i=0; i<ImageDimension; i++)
        {
        // add each index value to compute center of gravity
        cog->SetElement(i, cog->GetElement(i) + tcog->GetElement(i));
        // search bounding box
        if (bb->GetIndex(i) > tbb->GetIndex(i))
          {
          bb->SetIndex(i, tbb->GetIndex(i));
          }
        if (bb->GetSize(i) < tbb->GetSize(i))
          {
          bb->SetSize(i, tbb->GetSize(i));
          }
        }
      
      } // end of thread map iterator loop
    } // end of thread loop
    
  // compute the remainder of the statistics 
  // Calculate the size of pixel
  double physicalPixelSize = 1.0;
  for (i=0; i < ImageDimension; ++i)
    {
    physicalPixelSize *= this->GetInput()->GetSpacing()[i];
    }

  for (mapIt = m_LabelShape.begin();
       mapIt != m_LabelShape.end();
       ++mapIt)
    {
    // store labels
    m_Labels.push_back((*mapIt).first);
    
    // volume in physical units
    (*mapIt).second.m_VolumeInPhysicalUnits = (*mapIt).second.m_Volume * physicalPixelSize;
    
    for (int i=0; i<ImageDimension; i++)
      {
      // center of gravity 
      CenterOfGravityType * cog = &(*mapIt).second.m_CenterOfGravity;
      cog->SetElement(i, cog->GetElement(i) / static_cast<double>( (*mapIt).second.m_Volume ));
      
      // center of gravity in physical units
      CenterOfGravityType * cogpu = &(*mapIt).second.m_CenterOfGravityInPhysicalUnits;
      cogpu->SetElement(i, cog->GetElement(i) * this->GetInput()->GetSpacing()[i] + this->GetInput()->GetOrigin()[i]);
      
      // bounding box
      BoundingBoxType * bb = &(*mapIt).second.m_BoundingBox;
      bb->SetSize(i, bb->GetSize(i) - bb->GetIndex(i) + 1);
      }
    }
  
}

template<class ImageType>
void
LabelShapeImageFilter<ImageType>
::ThreadedGenerateData(const RegionType& outputRegionForThread,
         int threadId) 
{
  PixelType label;
  typedef ImageRegionConstIteratorWithIndex<ImageType> ImageIterator;
  typename ImageIterator::IndexType idx;
  ImageIterator it (this->GetInput(), outputRegionForThread);
  MapIterator mapIt;
  
  // support progress methods/callbacks
  ProgressReporter progress(this, threadId, outputRegionForThread.GetNumberOfPixels());

  // do the work
  while (!it.IsAtEnd())
    {
    label = it.Get();
    idx = it.GetIndex();
    
    // is the label already in this thread?
    mapIt = m_LabelShapePerThread[threadId].find( label );
    if (mapIt == m_LabelShapePerThread[threadId].end())
      {
      // create a new statistics object
      typedef typename MapType::value_type MapValueType;
      mapIt = m_LabelShapePerThread[threadId].insert( MapValueType(label, LabelShape()) ).first;
      // use current index to define first values of bounding box
      for (int i=0; i<ImageDimension; i++)
        {
        (*mapIt).second.m_BoundingBox.SetIndex(i, idx[i]);
        (*mapIt).second.m_BoundingBox.SetSize(i, idx[i]);
        }
      }

    // update the values for this label and this thread
    (*mapIt).second.m_Volume++;
    
    CenterOfGravityType * cog = &(*mapIt).second.m_CenterOfGravity;
    BoundingBoxType * bb = &(*mapIt).second.m_BoundingBox;
    
    for (int i=0; i<ImageDimension; i++)
      {
      // add each index value to compute center of gravity
      cog->SetElement(i, cog->GetElement(i) + idx[i]);
      // search bounding box
      if (bb->GetIndex(i) > idx[i])
        {
         bb->SetIndex(i, idx[i]);
        }
      if (bb->GetSize(i) < idx[i])
        {
         bb->SetSize(i, idx[i]);
        }
      }
    
    ++it;
    progress.CompletedPixel();
    }
}

template<class ImageType>
unsigned long
LabelShapeImageFilter<ImageType>
::GetVolume(PixelType label) const
{
  MapConstIterator mapIt;
  mapIt = m_LabelShape.find( label );
  if ( mapIt == m_LabelShape.end() )
    {
    // label does not exist
    itkExceptionMacro( << "Unknown label: " << static_cast< typename NumericTraits< PixelType >::PrintType >( label ) );
    }
  else
    {
    return (*mapIt).second.m_Volume;
    }
}

template<class ImageType>
typename LabelShapeImageFilter<ImageType>::CenterOfGravityType
LabelShapeImageFilter<ImageType>
::GetCenterOfGravity(PixelType label) const
{
  MapConstIterator mapIt;
  mapIt = m_LabelShape.find( label );
  if ( mapIt == m_LabelShape.end() )
    {
    // label does not exist
    itkExceptionMacro( << "Unknown label: " << static_cast< typename NumericTraits< PixelType >::PrintType >( label ) );
    }
  else
    {
    return (*mapIt).second.m_CenterOfGravity;
    }
}

template<class ImageType>
typename LabelShapeImageFilter<ImageType>::BoundingBoxType
LabelShapeImageFilter<ImageType>
::GetBoundingBox(PixelType label) const
{
  MapConstIterator mapIt;
  mapIt = m_LabelShape.find( label );
  if ( mapIt == m_LabelShape.end() )
    {
    // label does not exist
    itkExceptionMacro( << "Unknown label: " << static_cast< typename NumericTraits< PixelType >::PrintType >( label ) );
    }
  else
    {
    return (*mapIt).second.m_BoundingBox;
    }
}

template<class ImageType>
double
LabelShapeImageFilter<ImageType>
::GetVolumeInPhysicalUnits(PixelType label) const {
  MapConstIterator mapIt;
  mapIt = m_LabelShape.find( label );
  if ( mapIt == m_LabelShape.end() )
    {
    // label does not exist
    itkExceptionMacro( << "Unknown label: " << static_cast< typename NumericTraits< PixelType >::PrintType >( label ) );
    }
  else
    {
    return (*mapIt).second.m_VolumeInPhysicalUnits;
    }
}

template<class ImageType>
typename LabelShapeImageFilter<ImageType>::CenterOfGravityType
LabelShapeImageFilter<ImageType>
::GetCenterOfGravityInPhysicalUnits(PixelType label) const
{
  MapConstIterator mapIt;
  mapIt = m_LabelShape.find( label );
  if ( mapIt == m_LabelShape.end() )
    {
    // label does not exist
    itkExceptionMacro( << "Unknown label: " << static_cast< typename NumericTraits< PixelType >::PrintType >( label ) );
    }
  else
    {
    return (*mapIt).second.m_CenterOfGravityInPhysicalUnits;
    }
}

template <class ImageType>
void 
LabelShapeImageFilter<ImageType>
::PrintSelf(std::ostream& os, Indent indent) const
{
  Superclass::PrintSelf(os,indent);

  os << indent << "Number of labels: " << m_LabelShape.size()
     << std::endl;
}


}// end namespace itk
#endif
