import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F

import net_sphere

class Net(nn.Module):
    def __init__(self, upscale_factor):
        super(Net, self).__init__()

        self.relu = nn.ReLU()
        self.conv1 = nn.Conv2d(3, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(64, 64, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv4 = nn.Conv2d(32, 3 * upscale_factor ** 2, (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)

        self._initialize_weights()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pixel_shuffle(self.conv4(x))
        return x

    def _initialize_weights(self):
        init.orthogonal_(self.conv1.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv2.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv3.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv4.weight)



class BasicBlock(nn.Module):

    def __init__(self, ins, outs):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(ins, outs, (3,3), (1,1), padding=1) # different weight
        self.relu1 = nn.PReLU()

    def forward(self, x):
        out = self.conv1(x)
        out = self.relu1(out)
        return out




class ResBlock(nn.Module):
    def __init__(self, ins, outs):
        super(ResBlock, self).__init__()
        self.basic1 = BasicBlock(ins,ins)
        self.basic2 = BasicBlock(ins, ins)
        # self.conv1 = nn.Conv2d(ins, ins, (3,3), (1,1), padding=1) # different weight
        # self.relu1 = nn.PReLU()
        # self.conv2 = nn.Conv2d(ins, ins, (3,3), (1,1), padding=1) # different weight
        # self.relu2 = nn.PReLU()

    def forward(self, x):
        residual = x
        out = self.basic1(x)
        out = self.basic2(out)
        out += residual
        return out

class DenseBlock(nn.Module):
    def __init__(self, ins):
        super(DenseBlock, self).__init__()
        self.basic1 = BasicBlock(ins, 64)
        self.basic2 = BasicBlock(64, 32)
        self.basic3 = BasicBlock(96, 32)
        self.basic4 = BasicBlock(128, 32)
        self.basic5 = BasicBlock(160, 32)
        self.basic6 = BasicBlock(192, 32)
        self.basic7 = BasicBlock(224, 32)

    def forward(self, x):
        x = self.basic1(x)
        y1 = self.basic2(x)
        y1 = torch.cat((x, y1), 1)
        x = self.basic3(y1)
        y1 = torch.cat((x, y1), 1)
        x = self.basic4(y1)
        y1 = torch.cat((x, y1), 1)
        x = self.basic5(y1)
        y1 = torch.cat((x, y1), 1)
        x = self.basic6(y1)
        y1 = torch.cat((x, y1), 1)
        x = self.basic7(y1)
        y1 = torch.cat((x, y1), 1)
        return y1


class SICNNNet(nn.Module):
    def __init__(self, upscale_factor, batch_size, classnum):
        super(SICNNNet, self).__init__()
        # self.loss1 = torch.nn.L1Loss()
        # self.loss2 = torch.nn.L1Loss()
        # self.loss3 = torch.nn.L1Loss()
        # self._initialize_weights()
        self.cnnh = CNNHNet(upscale_factor, batch_size)
        self.cnnr = CNNRNet(upscale_factor, batch_size, classnum)

    def forward(self, input, target):
        SR_data = cnnh(input)
        newdata = torch.cat((input, SRdata), 0)
        # newlabel = torch.cat((target, target), 0)
        SI_feature, SI_score = cnnr(newdata)
        SI_feature = torch.norm(SI_feature)
        SI_feature_HR = SI_feature[0:batchsize, :]
        SI_feature_SR = SI_feature[batchsize:, :]

        # loss1 = self.loss1(output1, target)

        # loss3 = self.loss3(fc5_1, fc5_2)

        # return loss1 + loss2
        return SR_data, SI_feature_HR, SI_feature_SR, SI_score
        # loss 3



        # return output1,

    # def _initialize_weights(self):
        # init.orthogonal_(self.conv1.weight, init.calculate_gain('relu'))
        # init.orthogonal_(self.conv2.weight, init.calculate_gain('relu'))
        # init.orthogonal_(self.conv3.weight, init.calculate_gain('relu'))
        # init.orthogonal_(self.conv4.weight)


class CNNRNet(nn.Module):
    def __init__(self, upscale_factor, batch_size, classnum):
        super(CHHRNet, self).__init__()
        self.classnum = classnum
        self.basic1a = BasicBlock(3, 32)
        self.basic1b = BasicBlock(32, 64)
        self.res1 = ResBlock(64, 64)
        self.basic2 = BasicBlock(64, 128)
        self.res2 = ResBlock(128, 128)
        self.res3 = ResBlock(128, 128)
        self.basic3 = BasicBlock(128, 256)
        self.reslayer1 = []
        for i in range(5):
            self.reslayer1.append(ResBlock(256, 256))
            self.reslayer1[i].cuda()
        self.basic4 = BasicBlock(256, 512)
        self.reslayer2 = []
        for i in range(3):
            self.reslayer2.append(ResBlock(512, 512))
            self.reslayer2[i].cuda()
        self.fc5 = nn.Linear(512, 512)
        self.fc6 = net_sphere.AngleLinear(512, self.classnum)

    def forward(self, input):
        x = self.basic1a(input)
        x = self.basic1b(x)
        y1 = F.max_pool2d(x, 2, 2)
        x = self.res1(y1)
        x = self.basic2(x)
        y1 = F.max_pool2d(x, 2, 2)
        x = self.res2(y1)
        x = self.res3(x)
        x = self.basic3(x)
        y1 = F.max_pool2d(x, 2, 2)
        for i in range(5):
            x = self.reslayer1[i](x)
        x = self.basic4(x)
        y1 = F.max_pool2d(x, 2, 2)
        for i in range(3):
            x = self.reslayer2[i](x)

        x = self.fc5(x)
        output = self.fc6(x)
        return x, output
        # fea1 = x[0:self.batchsize, :]
        # fea2 = x[self.batchsize :, :]
        #
        # x = self.fc5(x)
        #
        #
        # return fea1, fea2
        # loss2
        # loss2 = self.loss2(fea1, fea2.detach())


class CNNHNet(nn.Module):
    def __init__(self, upscale_factor):
        super(CNNHNet, self).__init__()
        self.batchsize = batchsize
        self.dense1 = DenseBlock(3)
        self.deconv1 = nn.ConvTranspose2d(256, 256, (2,2), (2,2), padding=0) # ?
        self.relude1 = nn.PReLU()

        self.dense2 = DenseBlock(256)
        self.deconv2 = nn.ConvTranspose2d(256, 256, (2,2), (2,2), (0,0)) # ?
        self.relude2 = nn.PReLU()

        self.dense3 = DenseBlock(256)
        self.deconv3 = nn.ConvTranspose2d(256, 256, (5,5), (2,2), (2,2))
        self.relude3 = nn.PReLU()
        self.prebasic4_1 = BasicBlock(256, 64)
        self.prebasic4_2 = BasicBlock(64, 32)
        self.prebasic4_3 = BasicBlock(96, 32)
        self.gen = nn.Conv2d(128, 3, (5,5), (1,1), padding=2)
        self.tanh = nn.Tanh()

        self._initialize_weights()

    def forward(self, input):
        x = F.avg_pool2d(input, 4, 4)
        y1 = self.dense1(x)
        x = self.relude1(self.deconv1(y1))
        y1 = self.dense2(x)
        x = self.relude2(self.deconv2(y1))

        x = self.prebasic4_1(x)
        y1 = self.prebasic4_2(x)
        y1 = torch.cat((x, y1), 1)
        x = self.prebasic4_3(y1)
        x = torch.cat((x, y1), 1)

        output = self.tanh(self.gen(x)) # output
        # x = self.relu(self.conv1(x))
        # x = self.relu(self.conv2(x))
        # x = self.relu(self.conv3(x))
        # x = self.pixel_shuffle(self.conv4(x))
        return output

    def _initialize_weights(self):
        return null
        # init.orthogonal_(self.conv1.weight, init.calculate_gain('relu'))
        # init.orthogonal_(self.conv2.weight, init.calculate_gain('relu'))
        # init.orthogonal_(self.conv3.weight, init.calculate_gain('relu'))
        # init.orthogonal_(self.conv4.weight)
