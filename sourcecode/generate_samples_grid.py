"""
-------------------------------------------------
   File Name:     generate_samples_grid.py
   Author :       Zhonghao Huang
   Date:          2019/4/13
   Description :
-------------------------------------------------
"""

""" Generate single image samples from a particular depth of a model """

import argparse
import torch as th
import os
from torch.backends import cudnn
from MSG_GAN.GAN import Generator
from torch.nn.functional import interpolate
from scipy.misc import imsave
from torchvision.utils import save_image
from tqdm import tqdm

# turn on the fast GPU processing mode on
cudnn.benchmark = True

# define the device for the training script
device = th.device("cuda" if th.cuda.is_available() else "cpu")


# set the manual seed
# th.manual_seed(3)


def parse_arguments():
    """
    default command line argument parser
    :return: args => parsed command line arguments
    """

    parser = argparse.ArgumentParser()

    parser.add_argument("--generator_file", action="store", type=str,
                        help="pretrained weights file for generator", required=True)

    parser.add_argument("--latent_size", action="store", type=int,
                        default=256,
                        help="latent size for the generator")

    parser.add_argument("--depth", action="store", type=int,
                        default=9,
                        help="depth of the network. **Starts from 1")

    parser.add_argument("--out_depth", action="store", type=int,
                        default=6,
                        help="output depth of images. **Starts from 0")

    parser.add_argument("--num_samples", action="store", type=int,
                        default=300,
                        help="number of synchronized grids to be generated")

    parser.add_argument("--out_dir", action="store", type=str,
                        default="interp_animation_frames/",
                        help="path to the output directory for the frames")

    args = parser.parse_args()

    return args


def progressive_upscaling(images):
    """
    upsamples all images to the highest size ones
    :param images: list of images with progressively growing resolutions
    :return: images => images upscaled to same size
    """
    with th.no_grad():
        for factor in range(1, len(images)):
            images[len(images) - 1 - factor] = interpolate(
                images[len(images) - 1 - factor],
                scale_factor=pow(2, factor)
            )

    return images


def main(args):
    """
    Main function for the script
    :param args: parsed command line arguments
    :return: None
    """

    print("Creating generator object ...")
    # create the generator object
    gen = th.nn.DataParallel(Generator(
        depth=args.depth,
        latent_size=args.latent_size
    )).to(device)

    print("Loading the generator weights from:", args.generator_file)
    # load the weights into it
    gen.load_state_dict(
        th.load(args.generator_file)
    )

    # path for saving the files:
    save_path = args.out_dir

    print("Generating scale synchronized images ...")

    # generate the images:
    with th.no_grad():
        point = th.randn(63, args.latent_size).to(device)
        point = (point / point.norm()) * (args.latent_size ** 0.5)
        ss_images = gen(point)

    # resize the images:
    ss_images = progressive_upscaling(ss_images)
    ss_image = ss_images[args.out_depth]

    # save the ss_image in the directory
    # save_image(os.path.join(save_path, "sample.png"),
    #        ss_image.squeeze(0).permute(1, 2, 0).cpu())

    save_image(ss_image, os.path.join(save_path, "sample.png"), nrow=7,
               normalize=True, scale_each=True, padding=0)

    print("Generated %d images at %s" % (args.num_samples, save_path))


if __name__ == '__main__':
    main(parse_arguments())
