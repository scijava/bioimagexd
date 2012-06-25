#ifndef __itkBinaryThinning3DImageFilter_h
#define __itkBinaryThinning3DImageFilter_h

#include <itkNeighborhoodIterator.h>
#include <itkImageToImageFilter.h>
#include <itkImageRegionIteratorWithIndex.h>
#include <itkConstantBoundaryCondition.h>

namespace itk
{
/** \class BinaryThinning3DImageFilter
*
* \brief This filter computes one-pixel-wide skeleton of a 3D input image.
*
* This class is parametrized over the type of the input image
* and the type of the output image.
* 
* The input is assumed to be a binary image. All non-zero valued voxels
* are set to 1 internally to simplify the computation. The filter will
* produce a skeleton of the object.  The output background values are 0,
* and the foreground values are 1.
* 
* A 26-neighbourhood configuration is used for the foreground and a
* 6-neighbourhood configuration for the background. Thinning is performed
* symmetrically in order to guarantee that the skeleton lies medial within
* the object.
*
* This filter is a parallel thinning algorithm and is an implementation
* of the algorithm described in:
* 
* T.C. Lee, R.L. Kashyap, and C.N. Chu.
* Building skeleton models via 3-D medial surface/axis thinning algorithms.
* Computer Vision, Graphics, and Image Processing, 56(6):462--478, 1994.
* 
* To do: Make use of multi-threading.
*
* \author Hanno Homann, Oxford University, Wolfson Medical Vision Lab, UK.
* 
* \sa MorphologyImageFilter
* \ingroup ImageEnhancement MathematicalMorphologyImageFilters
*
* Changed the name of the class from itkBinaryThinningImageFilter3D to
* itkBinaryThinning3DImageFilter by Lassi Paavolainen. Everything else is
* same as in original filter.
*/

template <class TInputImage,class TOutputImage>
class BinaryThinning3DImageFilter :
    public ImageToImageFilter<TInputImage,TOutputImage>
{
public:
  /** Standard class typedefs. */
  typedef BinaryThinning3DImageFilter    Self;
  typedef ImageToImageFilter<TInputImage,TOutputImage> Superclass;
  typedef SmartPointer<Self> Pointer;
  typedef SmartPointer<const Self> ConstPointer;

  /** Method for creation through the object factory */
  itkNewMacro(Self);

  /** Run-time type information (and related methods). */
  itkTypeMacro( BinaryThinning3DImageFilter, ImageToImageFilter );

  /** Type for input image. */
  typedef   TInputImage       InputImageType;

  /** Type for output image: Skelenton of the object.  */
  typedef   TOutputImage      OutputImageType;

  /** Type for the region of the input image. */
  typedef typename InputImageType::RegionType RegionType;

  /** Type for the index of the input image. */
  typedef typename RegionType::IndexType  IndexType;

  /** Type for the pixel type of the input image. */
  typedef typename InputImageType::PixelType InputImagePixelType ;

  /** Type for the pixel type of the input image. */
  typedef typename OutputImageType::PixelType OutputImagePixelType ;

  /** Type for the size of the input image. */
  typedef typename RegionType::SizeType SizeType;

  /** Pointer Type for input image. */
  typedef typename InputImageType::ConstPointer InputImagePointer;

  /** Pointer Type for the output image. */
  typedef typename OutputImageType::Pointer OutputImagePointer;
  
  /** Boundary condition type for the neighborhood iterator */
  typedef ConstantBoundaryCondition< TInputImage > ConstBoundaryConditionType;
  
  /** Neighborhood iterator type */
  typedef NeighborhoodIterator<TInputImage, ConstBoundaryConditionType> NeighborhoodIteratorType;
  
  /** Neighborhood type */
  typedef typename NeighborhoodIteratorType::NeighborhoodType NeighborhoodType;

  /** Get Skelenton by thinning image. */
  OutputImageType * GetThinning(void);

  /** ImageDimension enumeration   */
  itkStaticConstMacro(InputImageDimension, unsigned int,
                      TInputImage::ImageDimension );
  itkStaticConstMacro(OutputImageDimension, unsigned int,
                      TOutputImage::ImageDimension );

#ifdef ITK_USE_CONCEPT_CHECKING
  /** Begin concept checking */
  itkConceptMacro(SameDimensionCheck,
    (Concept::SameDimension<InputImageDimension, 3>));
  itkConceptMacro(SameTypeCheck,
    (Concept::SameType<InputImagePixelType, OutputImagePixelType>));
  itkConceptMacro(InputAdditiveOperatorsCheck,
    (Concept::AdditiveOperators<InputImagePixelType>));
  itkConceptMacro(InputConvertibleToIntCheck,
    (Concept::Convertible<InputImagePixelType, int>));
  itkConceptMacro(IntConvertibleToInputCheck,
    (Concept::Convertible<int, InputImagePixelType>));
  itkConceptMacro(InputIntComparableCheck,
    (Concept::Comparable<InputImagePixelType, int>));
  /** End concept checking */
#endif

protected:
  BinaryThinning3DImageFilter();
  virtual ~BinaryThinning3DImageFilter() {};
  void PrintSelf(std::ostream& os, Indent indent) const;

  /** Compute thinning Image. */
  void GenerateData();

  /** Prepare data. */
  void PrepareData();

  /**  Compute thinning Image. */
  void ComputeThinImage();
  
  /**  isEulerInvariant [Lee94] */
  bool isEulerInvariant(NeighborhoodType neighbors, int *LUT);
  void fillEulerLUT(int *LUT);  
  /**  isSimplePoint [Lee94] */
  bool isSimplePoint(NeighborhoodType neighbors);
  /**  Octree_labeling [Lee94] */
  void Octree_labeling(int octant, int label, int *cube);


private:   
  BinaryThinning3DImageFilter(const Self&); //purposely not implemented
  void operator=(const Self&); //purposely not implemented

}; // end of BinaryThinning3DImageFilter class

} //end namespace itk

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkBinaryThinning3DImageFilter.txx"
#endif

#endif
