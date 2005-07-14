#! /usr/bin/env python
import Image

img=Image.open("merging.png")
img=img.resize((768,768))
img.save(open("merging2.png","w"))

