# Simple pygame program

# Import and initialize the pygame library
import pygame
from image_segmentation import getImageSegments, ImageSegment, sortImageSegments1, getRandomColor, BLACK, WHITE, SEGMENT
from datetime import datetime
import sys
import os, os.path
import pickle
import argparse
import ntpath
import copy

BASE_FOLDER = r'./img/'
iSeg, iPixel = 0, 0
PIXEL_DRAW_CT = 10
BEGIN = False
segments = None


def setupArgs():
  parser_ = argparse.ArgumentParser()
  parser_.add_argument('--imagepath', action='store', type=str, required=True)
  parser_.add_argument('--targetdirectory', action='store', type=str)
  parser_.add_argument('--randomwalk', action='store', type=int)
  parser_.add_argument('--referenceimage', action='store', type=str)
  return parser_


parser = setupArgs()
args = vars(parser.parse_args())
IMAGE_PATH = args.get('imagepath')
IMAGE_NAME = ntpath.basename(IMAGE_PATH)
IMAGE_PREFIX = ntpath.basename(os.path.splitext(IMAGE_PATH)[0])
TARGET_FOLDER = args.get('targetdirectory') or os.path.join(BASE_FOLDER, IMAGE_PREFIX)
RANDOM_WALK = args.get('randomwalk') or 0
REFERENCE_IMAGE = args.get('referenceimage') or None

print(f"randomwalk:{RANDOM_WALK}\nIMAGE_PATH:{IMAGE_PATH}\nIMAGE_NAME:{IMAGE_NAME}\nTARGET_FOLDER:{TARGET_FOLDER}\n")
# sys.exit()
not os.path.exists(TARGET_FOLDER) and os.mkdir(TARGET_FOLDER)
assert os.path.exists(TARGET_FOLDER)


def serialize(obj, fileName_, targetDir=None):
  with open(os.path.join(targetDir or TARGET_FOLDER, f"{fileName_}.pkl"), 'wb') as f:
    try:
      pickle.dump(obj, f)
      return True
    except Exception as e:
      print(e)
      return False


def deserialize(filePath):
  with open(filePath, 'rb') as f:
    try:
      return pickle.load(f)
    except Exception as e:
      print('Exception:'.format(e))
      return


def save(surface_, prefix=None, postfix=True):
  prefix = prefix or IMAGE_PREFIX
  postfix = f"_{str(datetime.now()).replace('-', '_').replace(':', '_').replace('.', '_').replace(' ', '_')}" if postfix else ''
  pygame.image.save(surface_, f"{TARGET_FOLDER}/{prefix}{postfix}.png")


def getColor(color_):
    return getRandomColor() if color_ == WHITE else color_


def flip(display):
    display.flip()


def getPixelCount(totalPixels, color_):
  if color_ == BLACK:
    return 2
  if totalPixels > 100000:
    return 75
  elif totalPixels > 50000:
    return 15
  elif totalPixels > 10000:
    return 10
  elif totalPixels > 5000:
    return 5
  return 2


def getSegments(image_, path=None):
  path = path or f"{os.path.join(TARGET_FOLDER, IMAGE_PREFIX)}.pkl"
  if os.path.exists(path):
    print(f"Image already processed. DeSerializing {path}")
    return deserialize(path)
  else:
    print(f"Processing Image for the first time.")
    segments_ = getImageSegments(image_)
    print('Now sorting image segments...')
    segments_ = sortImageSegments1(segments_, (w, h), sortBy=SEGMENT.POSITION, reverse=False, ignore=[])
    if segments_:
      if not serialize(segments_, IMAGE_PREFIX, targetDir=TARGET_FOLDER):
        print('Failed to serialize')
    return segments_


def getImage(imagePath):
  image_ = pygame.image.load(imagePath)
  return image_, *image_.get_rect().size


def draw():
  global segments, iSeg, iPixel, screen, color, pixelCount
  try:
    pixel = segments[iSeg].pixels[iPixel]
    screen.set_at(pixel, color)
  except Exception as e:
    # print(e)
    iSeg += 1
    iPixel = 0
    # save(screen)
    if iSeg >= len(segments):
        flip(pygame.display)
        return
    color = getColor(segments[iSeg].color)
    pixelCount = getPixelCount(len(segments[iSeg].pixels), color)
    print(f"Processing segment {iSeg}/{len(segments)}({len(segments[iSeg].pixels)}-{pixelCount}), orig color {segments[iSeg].color}, new color:{color}")


def preProcessSegments(segments_):
  segSize_ = {i: len(segment.pixels) for i, segment in enumerate(segments_)}
  color_ = getColor(segments_[iSeg].color)
  pixelCount_ = getPixelCount(len(segments_[iSeg].pixels), color_)
  return segSize_, color_, pixelCount_


image, w, h = getImage(IMAGE_PATH)
segments = getSegments(image)
segSize, color, pixelCount = preProcessSegments(segments)

if RANDOM_WALK:
  for i in range(RANDOM_WALK):
    surface = pygame.Surface((w, h))
    segmentsC = []
    for segment in segments:
      color = getColor(segment.color)
      segment_ = ImageSegment(color)
      segment_.pixels = copy.deepcopy(segment.pixels)
      for pixel in segment.pixels:
        surface.set_at(pixel, color)
      segmentsC.append(segment_)
    fileName = f"{i}_random_walk_{IMAGE_PREFIX}"
    print(f"({i})Saving...{fileName}")
    if not serialize(segmentsC, fileName, ):
      print(f"Failed to serialize {fileName}")
      continue
    save(surface, fileName, postfix=False)
  sys.exit()

if REFERENCE_IMAGE:
  segments = getSegments(image, REFERENCE_IMAGE)
  print(segments[39])
  segSize, color, pixelCount = preProcessSegments(segments)

print(f"Processing segment {iSeg}/{len(segments)}({len(segments[iSeg].pixels)}-{pixelCount}), orig color {segments[iSeg].color}, new color:{color}")
running = True
pygame.init()
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))


while running:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
      # save(screen)
      pygame.quit()
    elif event.type == pygame.KEYUP:
      if event.key == pygame.K_SPACE:
          BEGIN = not BEGIN

  if not BEGIN:
    continue

  if iSeg >= len(segSize):
    flip(pygame.display)
    continue

  pCtr = range(iPixel, min(segSize[iSeg]+1, iPixel+pixelCount))
  for i in pCtr:
    iPixel = i
    draw()
  flip(pygame.display)
