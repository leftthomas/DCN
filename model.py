import torch
from capsule_layer import CapsuleLinear
from torch import nn
from torch.nn import functional as F

from resnet import resnet18, resnet34, resnet50, resnext50_32x4d


def set_bn_eval(m):
    classname = m.__class__.__name__
    if classname.find('BatchNorm2d') != -1:
        m.eval()


class Model(nn.Module):
    def __init__(self, backbone_type, capsule_num, feature_dim):
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

        # Capsule Layer
        self.hidden = CapsuleLinear(capsule_num, 512 * expansion, 512 // expansion)
        self.refactor = CapsuleLinear(1, 512 // expansion, feature_dim, capsule_num, False)

    def forward(self, x):
        local_features = self.features(x)
        local_features = torch.flatten(local_features, start_dim=2).permute(0, 2, 1).contiguous()
        hidden_capsules, _ = self.hidden(local_features)
        out_capsule, _ = self.refactor(hidden_capsules)
        global_feature = F.normalize(out_capsule.squeeze(dim=1), dim=-1)
        return global_feature
