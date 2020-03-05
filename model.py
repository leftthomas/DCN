import torch
from torch import nn
from torch.nn import functional as F

from resnet import resnet18, resnet34, resnet50, resnext50_32x4d


def set_bn_eval(m):
    classname = m.__class__.__name__
    if classname.find('BatchNorm2d') != -1:
        m.eval()


class Model(nn.Module):
    def __init__(self, backbone_type, feature_dim):
        super().__init__()

        # Backbone Network
        backbones = {'resnet18': (resnet18, 1), 'resnet34': (resnet34, 1), 'resnet50': (resnet50, 4),
                     'resnext50': (resnext50_32x4d, 4)}
        backbone, expansion = backbones[backbone_type]
        self.features = []
        for name, module in backbone(pretrained=True).named_children():
            if isinstance(module, nn.AdaptiveAvgPool2d) or isinstance(module, nn.Linear):
                continue
            self.features.append(module)
        self.features = nn.Sequential(*self.features)

        # Refactor Layer
        self.refactor = nn.Linear(512 * expansion, feature_dim, bias=False)

    def forward(self, x):
        global_feature = F.adaptive_avg_pool2d(self.features(x), output_size=(1, 1))
        global_feature = torch.flatten(global_feature, start_dim=1)
        global_feature = self.refactor(global_feature)
        global_feature = F.normalize(global_feature, dim=-1)
        return global_feature
