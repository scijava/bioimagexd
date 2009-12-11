/*=========================================================================

  Program:   Insight Segmentation & Registration Toolkit
  Module:    $RCSfile: itkLabelShapeImageFilter.h,v $
  Language:  C++
  Date:      $Date: 2005/05/02 19:27:25 $
  Version:   $Revision: 1.4 $

  Copyright (c) Insight Software Consortium. All rights reserved.
  See ITKCopyright.txt or http://www.itk.org/HTML/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even 
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
     PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#ifndef __itkLabelShapeImageFilter_h
#define __itkLabelShapeImageFilter_h

#include "itkImageToImageFilter.h"
#include "itkNumericTraits.h"
#include "itkArray.h"
#include "itkSimpleDataObjectDecorator.h"
#include "itk_hash_map.h"
#include "itkFixedArray.h"
#include "itkImageRegion.h"
#include <vector>

namespace itk {

/** \class LabelShapeImageFilter 
 * \brief Given a label map, compute center of gravity and bounding box of each component
 *
 * LabelShapeImageFilter computes the center of gravity and bounding box
 * of regions defined via a label map.  The image should be integral type.
 * The filter needs all of its input image.  It behaves as a filter with
 * an input and output. Thus it can be inserted in a pipline with other
 * filters and the statistics will only be recomputed if a downstream
 * filter changes.
 *
 * The filter passes its intensity input through unmodified.  The filter is
 * threaded. It computes statistics in each thread then combines them in
 * its AfterThreadedGenerate method.
 *
 * \ingroup MathematicalStatisticsImageFilters
 */
template<class ImageType>
class ITK_EXPORT LabelShapeImageFilter : 
    public ImageToImageFilter<ImageType, ImageType>
{
public:
  /** Standard Self typedef */
  typedef LabelShapeImageFilter Self;
  typedef ImageToImageFilter<ImageType, ImageType>  Superclass;
  typedef SmartPointer<Self> Pointer;
  typedef SmartPointer<const Self>  ConstPointer;
  
  /** Method for creation through the object factory. */
  itkNewMacro(Self);  

  /** Runtime information support. */
  itkTypeMacro(LabelShapeImageFilter, ImageToImageFilter);
  
  /** Label image related typedefs. */
  typedef typename ImageType::Pointer ImagePointer;
  typedef typename ImageType::RegionType RegionType ;
  typedef typename ImageType::SizeType SizeType ;
  typedef typename ImageType::IndexType IndexType ;
  typedef typename ImageType::PixelType PixelType ;
  
  /** Image related typedefs. */
  itkStaticConstMacro(ImageDimension, unsigned int,
        ImageType::ImageDimension ) ;

//   /** Smart Pointer type to a DataObject. */
//   typedef typename DataObject::Pointer DataObjectPointer;
// 
//   /** Type of DataObjects used for scalar outputs */
//   typedef SimpleDataObjectDecorator<PixelType> RealObjectType;

  /** type used for Center of gravity */
  typedef typename itk::FixedArray<double, ImageDimension> CenterOfGravityType;
  
  /** type used for bounding box */
  typedef typename itk::ImageRegion<ImageDimension> BoundingBoxType;
  
  /** Statistics stored per label */
  class LabelShape
  {
  public:

    // default constructor
    LabelShape()
      {
      // initialized to the default values
      m_Volume = 0;
      m_CenterOfGravity = CenterOfGravityType();
      m_BoundingBox = BoundingBoxType();
      
      m_VolumeInPhysicalUnits = 0;
      m_CenterOfGravityInPhysicalUnits = CenterOfGravityType();
	  for (int i = 0; i < ImageDimension; ++i)
	    {
		m_CenterOfGravity[i] = 0.0;
		m_CenterOfGravityInPhysicalUnits[i] = 0.0;
	    }
      //m_BoundingBoxInPhysicalUnits = itk::ImageRegion<ImageDimension>;
      }

    // need copy constructor because of smart pointer to histogram
    LabelShape(const LabelShape& l)
      {
      m_Volume = l.m_Volume;
      m_CenterOfGravity = l.m_CenterOfGravity;
      m_BoundingBox = l.m_BoundingBox;
      m_VolumeInPhysicalUnits = l.m_VolumeInPhysicalUnits;
      m_CenterOfGravityInPhysicalUnits = l.m_CenterOfGravityInPhysicalUnits;
      //m_BoundingBoxInPhysicalUnits = l.m_BoundingBoxInPhysicalUnits
      }

    // added for completeness
    LabelShape& operator= (const LabelShape& l)
      {
      m_Volume = l.m_Volume;
      m_CenterOfGravity = l.m_CenterOfGravity;
      m_BoundingBox = l.m_BoundingBox;
      m_VolumeInPhysicalUnits = l.m_VolumeInPhysicalUnits;
      m_CenterOfGravityInPhysicalUnits = l.m_CenterOfGravityInPhysicalUnits;
      //m_BoundingBoxInPhysicalUnits = l.m_BoundingBoxInPhysicalUnits
      }
      
    unsigned long m_Volume;
    CenterOfGravityType m_CenterOfGravity;
    BoundingBoxType m_BoundingBox;
    
    double m_VolumeInPhysicalUnits;
    CenterOfGravityType m_CenterOfGravityInPhysicalUnits;
    //BoundingBoxType m_BoundingBoxInPhysicalUnits;
  };
  
  /** Type of the map used to store data per label */
  typedef itk::hash_map<PixelType, LabelShape> MapType;
  typedef typename itk::hash_map<PixelType, LabelShape>::iterator MapIterator;
  typedef typename itk::hash_map<PixelType, LabelShape>::const_iterator MapConstIterator;

  /** Set the label image */
  void SetInput(ImageType *input)
    {
      // Process object is not const-correct so the const casting is required.
      this->SetNthInput(0, const_cast<ImageType *>(input) );
    }

  /** Get the label image */
  ImageType * GetInput()
    {
      return static_cast<ImageType*>(const_cast<DataObject *>(this->ProcessObject::GetInput(0)));
    }

  /** Does the specified label exist? Can only be called after a call
   * a call to Update(). */
  bool HasLabel(PixelType label) const
    {
      return m_LabelShape.find(label) != m_LabelShape.end();
    }

  /** Get the number of labels used */
  unsigned long GetNumberOfLabels() const
    {
      return m_LabelShape.size();
    }

  /** Get the labels used */
  const std::vector<PixelType>& GetLabels() const
    {
      return m_Labels;
    }

  
  /** Return the number of pixels for a label. */
  unsigned long GetVolume(PixelType label) const;
  
  /** Return the center of gravity of a label. */
  CenterOfGravityType GetCenterOfGravity(PixelType label) const;
  
  /** Return the bounding box of a label. */
  BoundingBoxType GetBoundingBox(PixelType label) const;
   
  /** Return the volume of a label in physical units. */
  double GetVolumeInPhysicalUnits(PixelType label) const;
  
  /** return the center of gravity of a label in physical units. */
  CenterOfGravityType GetCenterOfGravityInPhysicalUnits(PixelType label) const;
  
//   /** Return the bounding box of a label in physical units. */
//   //itk::ImageRegion<ImageDimension> GetBoundingBoxInPhysicalUnits(PixelType label) const;


protected:
  LabelShapeImageFilter();
  ~LabelShapeImageFilter(){};
  void PrintSelf(std::ostream& os, Indent indent) const;

  /** Pass the input through unmodified. Do this by Grafting in the AllocateOutputs method. */
  void AllocateOutputs();      

  /** Initialize some accumulators before the threads run. */
  void BeforeThreadedGenerateData ();
  
  /** Do final mean and variance computation from data accumulated in threads. */
  void AfterThreadedGenerateData ();
  
  /** Multi-thread version GenerateData. */
  void  ThreadedGenerateData (const RegionType& outputRegionForThread, int threadId) ;

  // Override since the filter needs all the data for the algorithm
  void GenerateInputRequestedRegion();

  // Override since the filter produces all of its output
  void EnlargeOutputRequestedRegion(DataObject *data);


private:
  LabelShapeImageFilter(const Self&); //purposely not implemented
  void operator=(const Self&); //purposely not implemented

  std::vector<MapType>  m_LabelShapePerThread;
  MapType        m_LabelShape;
  std::vector<PixelType> m_Labels;

} ; // end of class

} // end namespace itk
  
#ifndef ITK_MANUAL_INSTANTIATION
#include "itkLabelShapeImageFilter.txx"
#endif

#endif
