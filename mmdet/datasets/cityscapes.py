import os
import os.path as osp
from .coco import CocoDataset
import numpy as np
from .registry import DATASETS
from mmcv.parallel import DataContainer as DC
from .pipelines.formating import to_tensor
import pdb

@DATASETS.register_module
class CityscapesDataset(CocoDataset):
    def __init__(self,
                 ann_file,
                 pipeline,
                 data_root=None,
                 img_prefix=None,
                 seg_prefix=None,
                 # flow_prefix=None,
                 ref_prefix=None,
                 proposal_file=None,
                 test_mode=False,
                 offsets=None):
        super(CityscapesDataset, self).__init__(        
                 ann_file=ann_file,
                 pipeline=pipeline,
                 data_root=data_root,
                 img_prefix=img_prefix,
                 seg_prefix=seg_prefix,
                 # flow_prefix=flow_prefix,
                 ref_prefix=ref_prefix,
                 proposal_file=proposal_file,
                 test_mode=test_mode)

        self.offsets = offsets

    CLASSES = ('person', 'rider', 'car', 'truck', 'bus', 'train', 
               'motorcycle', 'bicycle')

    # CLASSES_ALL = ('car','truck', 'person', 'rider','bicycle','bus',
    #                'motorcycle','train', 'road', 'sidewalk', 'building',
    #                'wall','fence','pole','traffic_light','traffic_sign',
    #                'vegetation','terrain','sky')
    # all classes following the "cityscapes_panoptic.json"
    # trainId2cat = {0:'road',1:'sidewalk',2:'building',3:'wall',4:'fence',5:'pole',
    #             6:'traffic_light',7:'traffic_sign',8:'vegetation',9:'terrain',
    #             10:'sky',11:'person',12:'rider',13:'car',14:'truck',15:'bus',16:'train',
    #             17:'motorcycle',18:'bicycle'}

    # trainId2label = {11:1, 12:2, 13:3,  14:4, 15:5, 16:6, 17:7, 18:8, 
    #             0:9, 1:10, 2:11, 3:12, 4:13, 5:14, 6:15, 7:16, 8:17, 9:18, 10:19, 
    #             -1:0, 255:0}
    # label2semantic = {i+1:i+1 for i in trainId2cat.keys()}


    def pre_pipeline(self, results):
        results['img_prefix'] = self.img_prefix
        results['seg_prefix'] = self.seg_prefix
        # results['flow_prefix'] = self.flow_prefix
        results['ref_prefix'] = self.ref_prefix
        results['proposal_file'] = self.proposal_file
        results['bbox_fields'] = []
        results['mask_fields'] = []
        # results['trainId2label'] = self.trainId2label


    # to sample neighbor frame from offsets=[-1, +1]
    def prepare_train_img(self, idx):
        img_info = self.img_infos[idx]
        ann_info = self.get_ann_info(idx)
        iid = img_info['id']
        filename = img_info['filename']
        # Cityscapes - specific filename
        fid = int(filename.split('_')[-2])
        suffix = '_'+filename.split('_')[-1]
        # offsets = [-1, 1] for Cityscapes
        offsets = self.offsets.copy()
        # random sampling of neighbor frame id [-1, 1] 
        m = np.random.choice(offsets)
        ref_filename = filename.replace(
                '%06d'%fid+suffix, 
                '%06d'%(fid+m)+suffix) if fid >= 1 else filename
        img_info['ref_filename'] = ref_filename
        results = dict(img_info=img_info, ann_info=ann_info)

        if self.proposals is not None:
            results['proposals'] = self.proposals[idx]
        self.pre_pipeline(results)
        ### semantic segmentation label (only for target frame)
        # Cityscapes - specific filename
        seg_filename = osp.join(
                results['seg_prefix'], 
                results['ann_info']['seg_map'].replace(
                        'leftImg8bit',
                        'gtFine_labelTrainIds'))
        results['ann_info']['seg_filename'] = seg_filename

        # NO ref_ann_info for cityscapes - Fuse model
        # ref_seg_filename = osp.join(results['seg_prefix'], 
        #         results['ref_ann_info']['seg_map'].replace(
        #                 'leftImg8bit',
        #                 'gtFine_labelTrainIds'))
        # results['ref_ann_info']['seg_filename'] = ref_seg_filename

        return self.pipeline(results)


    ###### CHECK: NOT USING ?
    # def prepare_pano_test_img(self, idx):
    #     pdb.set_trace()
    #     img_info = self.img_infos[idx]
    #     results = dict(img_info=img_info)
    #     if self.proposals is not None:
    #         results['proposals'] = self.proposals[idx]
    #     self.pre_pipeline(results)
    #     return self.pipeline(results)

    # #### For pano_track training
    # # outputs two images with same idx, but different transformation.
    # def prepare_single_train_img(self, idx):
    #     img_info = self.img_infos[idx]
    #     ann_info = self.get_ann_info(idx)
    #     results = dict(img_info=img_info, ann_info=ann_info)
    #     if self.proposals is not None:
    #         results['proposals'] = self.proposals[idx]
    #     self.pre_pipeline(results)
    #     return self.pipeline(results)

    # def prepare_train_img(self, idx):
        
    #     data = self.prepare_single_train_img(idx)
    #     ref_data = self.prepare_single_train_img(idx)
    #     if data is None or ref_data is None:
    #         return None

    #     data['ref_img'] = ref_data['img']
    #     data['ref_bboxes'] = ref_data['gt_bboxes']
    #     data['ref_obj_ids'] = ref_data['gt_obj_ids']
    #     data['ref_masks'] = ref_data['gt_masks']
    #     # data['gt_pids'] BELOW
    #     # gt obj ids attribute did not exist in current annotation
    #     # we added it.
    #     ref_ids = ref_data['gt_obj_ids'].data.numpy().tolist()
    #     gt_ids = data['gt_obj_ids'].data.numpy().tolist()
    #     # compute matching of reference frame with current frame
    #     # 0 denote there is no matching
    #     # corresponding reference index ** +1 ** , if no match, give ZERO.
    #     gt_pids = [ref_ids.index(i)+1 if i in ref_ids else 0 for i in gt_ids]
    #     data['gt_pids'] = DC(to_tensor(gt_pids))
    #     return data
