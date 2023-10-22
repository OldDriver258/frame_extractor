#!user/bin/env python
# -*- coding:utf-8 -*-
# @File     : extractor.py
# @Auther   : Zhang.Yuchen
# @Time     : 2023-10-22
# @Descript : 从一段视频中提取指定的帧数, 并且交错合成这些帧, 并生成用于打印的 pdf 文件, 用于手摇动画机中的动画纸的制作

import os
import re
import argparse
import cv2
import math
import numpy
import img2pdf
from tqdm import tqdm

supported_video_ext = ('.avi', '.mp4')
supported_frame_ext = ('.jpg', '.png')
pdf_print_a4_px     = (3508, 2480)
pdf_print_dpi       = 300
mm_per_inch         = 25.4
bg_color            = 255

class FrameExtractor:
    def __init__(self, video_file, output_dir, frame_ext='.jpg'):
        """Extract frames from video file and save them under a given output directory.

        Args:
            video_file (str)   : input video filename
            output_dir (str)   : output directory where video frames will be extracted
            frame_ext  (str)   : extracted frame file format
        """
        # Check if given video file exists -- abort otherwise
        if os.path.exists(video_file):
            self.video_file = video_file
        else:
            raise FileExistsError("video file {} does not exist.".format(video_file))
        
        # Create output directory for storing extracted frames
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.output_frame_dir = os.path.join(output_dir, 'frame')
        if not os.path.exists(self.output_frame_dir):
            os.makedirs(self.output_frame_dir)
        self.output_frame_top_dir = os.path.join(output_dir, 'frame_top')
        if not os.path.exists(self.output_frame_top_dir):
            os.makedirs(self.output_frame_top_dir)
        self.output_frame_bottom_dir = os.path.join(output_dir, 'frame_bottom')
        if not os.path.exists(self.output_frame_bottom_dir):
            os.makedirs(self.output_frame_bottom_dir)
        self.output_frame_offset_dir = os.path.join(output_dir, 'frame_offset')
        if not os.path.exists(self.output_frame_offset_dir):
            os.makedirs(self.output_frame_offset_dir)
        self.output_frame_offset_resize_dir = os.path.join(output_dir, 'frame_offset_resize')
        if not os.path.exists(self.output_frame_offset_resize_dir):
            os.makedirs(self.output_frame_offset_resize_dir)
        self.output_frame_pdf_dir = os.path.join(output_dir, 'frame_pdf')
        if not os.path.exists(self.output_frame_pdf_dir):
            os.makedirs(self.output_frame_pdf_dir)
        self.output_video_file = os.path.join(output_dir, 'output.mp4')
        self.output_pdf_file = os.path.join(output_dir, 'output.pdf')
            
        # Get extracted frame file format
        self.frame_ext = frame_ext
        if frame_ext not in supported_frame_ext:
            raise ValueError("Not supported frame file format: {}".format(frame_ext))
        else:
            self.frame_ext = frame_ext
            
        # Capture given video stream
        self.video = cv2.VideoCapture(self.video_file)
        
        # Get video fps
        self.video_fps = self.video.get(cv2.CAP_PROP_FPS)
            
        # Get video size
        self.video_size = (int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                           int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH)))
        
        # Get video length in frames
        self.video_length = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_second = self.video_length / self.video_fps
        
    def video_detail(self, frame, size_px, size_mm):
        print("#. Video  file path      : {}".format(self.video_file))
        print("#. Video  file size      : (height={}px, width={}px)".format(self.video_size[0], self.video_size[1]))
        print("#. Video  file second    : {}".format(self.video_second))
        print("#. Video  file fps       : {}".format(self.video_fps))
        print("#. Video  file frams     : {}".format(self.video_length))
        print("#. Output file frams     : {}".format(frame))
        print("#. Output file size      : (height={}px, width={}px)".format(size_px[0], size_px[1]))
        print("#. Output file size      : (height={}mm, width={}mm)".format(size_mm[0], size_mm[1]))
        print("#. Output file dir       : {}".format(self.output_dir))
            
    def extract(self, args_frm, args_size):
        """extrace video with specified parameter

        Args:
            args_frm (int): set the number of extracted frame
            args_size (tuple(float, float)): set the size of frame in mm
        """
        # Sets the number of frames extracted
        if args_frm != -1:
            self.sample_frm = args_frm
        else:
            self.sample_frm = self.video_length
        
        # Sets the extracted frame size
        output_height    = math.ceil(args_size[0] * pdf_print_dpi / 25.4)
        output_width     = math.ceil(args_size[1] * pdf_print_dpi / 25.4)
        output_size      = (output_height, output_width)

        # Show video detail message
        self.video_detail(self.sample_frm, output_size, args_size)
        
        '''Step1. 
        Extracts the specified number of frames and generates the image file and preview video
        '''
        # Set extract process bar
        ext_pbar = tqdm(total=self.video_length)
        ext_pbar.set_description('Extract frame')
        
        # Cteate preview video
        self.output_video = cv2.VideoWriter(self.output_video_file,
                                            cv2.VideoWriter_fourcc('m','p','4','v'),
                                            self.sample_frm / self.video_second, self.video_size)

        frame_cnt      = 0
        frame_cnt_f    = 0
        file_cnt       = 0
        success        = True
    
        while success:
            # Get frame
            self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_cnt - 1)
            success, frame = self.video.read()
            
            # Extract frame to file
            curr_frame_filename = os.path.join(self.output_frame_dir, 
                                               "{:08d}{}".format(file_cnt, self.frame_ext))
            cv2.imwrite(curr_frame_filename, frame)
            
            # Generate preview video
            self.output_video.write(frame)
            
            # Split the top and bottom parts of frame
            curr_frame_filename = os.path.join(self.output_frame_top_dir, 
                                               "{:08d}{}".format(file_cnt, self.frame_ext))
            cv2.imwrite(curr_frame_filename, 
                        frame[0:int(self.video_size[0] / 2), 0:self.video_size[1]])
            curr_frame_filename = os.path.join(self.output_frame_bottom_dir, 
                                               "{:08d}{}".format(file_cnt, self.frame_ext))
            cv2.imwrite(curr_frame_filename, 
                        frame[int(self.video_size[0] / 2):self.video_size[0], 0:self.video_size[1]])
            
            if file_cnt == self.sample_frm - 1:
                break
            
            # Get next frame
            # print("cnt[{}] = {} => {}".format(file_cnt, frame_cnt_f, frame_cnt))
            frame_old    = frame_cnt
            frame_cnt_f += self.video_length / self.sample_frm
            frame_cnt    = math.ceil(frame_cnt_f)
            file_cnt    += 1
            
            if frame_cnt_f + (self.video_length / self.sample_frm) > self.video_length - 1:
                frame_cnt = self.video_length - 1

            ext_pbar.update(frame_cnt - frame_old)
        ext_pbar.update()
        
        '''Step2.
        Divid frame image into the upper and lower parts, and composite offset image and 
        scale new image to specified size
        '''
        # Set composite process bar
        comp_pbar = tqdm(total=self.sample_frm)
        comp_pbar.set_description('Composite frame')
        
        # Composite offset and resized frame
        for index in range(int(self.sample_frm)):
            # Calc offset index
            index_bottom = int(index)
            if index == 0:
                index_top = int(self.sample_frm - 1)
            else:
                index_top = int(index_bottom - 1)
            
            # Read top and bottom parts of frame
            curr_frame_filename = os.path.join(self.output_frame_top_dir, 
                                               "{:08d}{}".format(index_top, self.frame_ext))
            curr_top_frame = cv2.imread(curr_frame_filename)
            curr_frame_filename = os.path.join(self.output_frame_bottom_dir, 
                                               "{:08d}{}".format(index_bottom, self.frame_ext))
            curr_bottom_frame = cv2.imread(curr_frame_filename)
            
            # Composite top and bottom parts of frame
            frame = numpy.vstack((curr_top_frame, curr_bottom_frame))
            curr_frame_filename = os.path.join(self.output_frame_offset_dir, 
                                               "{:08d}{}".format(index, self.frame_ext))
            cv2.imwrite(curr_frame_filename, frame)
            
            # Scale image to specified size
            curr_frame_filename = os.path.join(self.output_frame_offset_resize_dir, 
                                               "{:08d}{}".format(index, self.frame_ext))
            cv2.imwrite(curr_frame_filename, cv2.resize(frame, output_size))
            
            comp_pbar.update()
        
        '''Step3.
        Typeset the image onto a4 paper and generate the corresponding printed pdf file
        '''
        # Generate pdf page
        page_row        = math.floor(pdf_print_a4_px[0] / output_size[0])
        page_col        = math.floor(pdf_print_a4_px[1] / output_size[1])
        page_frm        = page_row * page_col
        page_total      = int(self.sample_frm / page_frm)
        page_row_inr    = math.floor((pdf_print_a4_px[0] - page_row * output_size[0]) / (page_row + 1))
        page_col_inr    = math.floor((pdf_print_a4_px[1] - page_col * output_size[1]) / (page_col + 1))
        end_flag        = False
        
        # Set process bar
        pdf_pbar = tqdm(total=(page_total + 1))
        pdf_pbar.set_description('Generate pdf')  
        
        for page in range(page_total):
            # Generate blank a4 image
            page_bg = numpy.full((pdf_print_a4_px[0], pdf_print_a4_px[1], 3), bg_color, numpy.uint8)
            
            # Typeset images onto one page
            for row in range(page_row):
                for col in range(page_col):
                    index = page * page_frm + row * page_row + col
                    if (index >= self.sample_frm):
                        end_flag = True
                        break

                    curr_frame_filename = os.path.join(self.output_frame_offset_resize_dir, 
                                                       "{:08d}{}".format(index, self.frame_ext))
                    curr_frame = cv2.imread(curr_frame_filename)
                    
                    # Overlay image to the background
                    y_offset = (row + 1) * page_row_inr + row * output_size[0]
                    x_offset = (col + 1) * page_col_inr + col * output_size[1]
                    page_bg[y_offset:y_offset + output_size[0], x_offset:x_offset + output_size[1]] = curr_frame
                    
                if end_flag:
                    break
            
            # Generate one page of a4 paper
            curr_frame_filename = os.path.join(self.output_frame_pdf_dir, 
                                               "{:08d}{}".format(page, self.frame_ext))
            cv2.imwrite(curr_frame_filename, page_bg)
            
            pdf_pbar.update()

        # Get pdf image list and Set pdf layout
        frame_list = sorted(os.listdir(self.output_frame_pdf_dir))
        frame_list = [os.path.join(self.output_frame_pdf_dir, i) for i in frame_list]
        input_a4   = (img2pdf.mm_to_pt(210),img2pdf.mm_to_pt(297))
        layout_fun = img2pdf.get_layout_fun(input_a4)
        
        # Generate print pdf file
        with open(self.output_pdf_file, 'wb') as f:
            f.write(img2pdf.convert(frame_list, layout_fun=layout_fun))
        
        pdf_pbar.update()
        
        '''End
        '''

def check_frm_param(s):
    s_ = int(s)
    if (s_ <= 0) and (s_ != -1):
        raise argparse.ArgumentTypeError("Please give a positive number of extract frame number.")
    return s_

def check_size_param(str):
    if not (re.match(r'\(\d+,\d+\)', str)):
        raise argparse.ArgumentTypeError("Please give a correct size pattern. eg: (96,96)")
    size   = re.findall(r'\d+', str)
    height = float(size[0])
    width  = float(size[1])
    if (height <= 0) or (width <= 0):
        raise argparse.ArgumentTypeError("Please give a normal length value, unit is millimeters.")
    return tuple((height, width))

def main():
    # Set up a parser for command line arguments
    parser = argparse.ArgumentParser(description="Extract the frames in the video and generate preview "
                                     "video, splice the top half of the frame with the bottom half and "
                                     "generate a printed pdf file.")
    parser.add_argument('-v', '--video', metavar='vidio_file', type=str, required=True,
                        help='Set the video files to be processed')
    parser.add_argument('-o', '--output-root', metavar='output_dir', type=str, default='extracted_frames', 
                        help="Set the root directory for the output video (default: ./extracted_frames)")
    parser.add_argument('-f', '--frame', metavar='frame_count', type=check_frm_param, default=-1,
                        help="The total number of video frames extracted (default: extract all frames)")
    parser.add_argument('-s', '--size', metavar='(height,width)', type=check_size_param, default='(96,96)',
                        help="Set the (height,width) of the output frame in mm, the dpi is 300 (default: 96mm)")

    args = parser.parse_args()
    
    # Extract frames from a (single) given video file
    if args.video:
        # Setup video extractor for given video file
        video_basename = os.path.basename(args.video).split('.')[0]
        # Check video file extension
        video_ext = os.path.splitext(args.video)[-1]
        if video_ext not in supported_video_ext:
            raise ValueError("Not supported video file format: {}".format(video_ext))
        # Set extracted frames output directory
        output_dir = os.path.join(args.output_root, 'output_{}'.format(video_basename))
        # Set up video extractor for given video file
        extractor = FrameExtractor(video_file=args.video, output_dir=output_dir)
        # Extract frames
        extractor.extract(args.frame, args.size)

if __name__ == '__main__':
    main()