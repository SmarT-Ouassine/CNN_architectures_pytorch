
import config
import  torch
from tqdm import tqdm
from dataset import get_loaders
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
from utils import plot_to_tensorboard, save_checkpoint, load_checkpoint
from  vgg_batchNorm import *

from Resnet34 import Resnet34
from vgg19 import *
from  resnet101 import Resnet101
from mobileNetV1 import MobileNetV1

def main():

    if config.MODEL=="vgg":
        print(" creation of architecture vgg")
        model = VGG_batchNorm(in_channels=config.IN_CHANNELS, num_classes=config.NUM_CLASSES).to(device=config.DEVICE)
        optimizer = optim.SGD(model.parameters(), momentum=0.9, lr=1e-2, weight_decay=5e-4)

    elif config.MODEL =="resnet34":
        print(" creation of architecture Resnet34")
        model = Resnet34(in_channels=config.IN_CHANNELS, num_classes=config.NUM_CLASSES).to(device=config.DEVICE)
        optimizer = optim.SGD(model.parameters(), momentum=0.9, lr=1e-2, weight_decay=5e-4)

    elif config.MODEL =="resnet101":
        print(" creation of architecture Resnet101")
        model = Resnet101(in_channels=config.IN_CHANNELS, num_classes=config.NUM_CLASSES).to(device=config.DEVICE)
        optimizer = optim.SGD(model.parameters(), momentum=0.9, lr=1e-2, weight_decay=5e-4)

    elif config.MODEL =="mobileNetV1":
        print(" creation of architecture mobileNetV1")
        model = MobileNetV1(in_channels=config.IN_CHANNELS, shallow=False, num_classes=config.NUM_CLASSES).to(device=config.DEVICE)
        optimizer = optim.RMSprop(model.parameters(), lr=0.01)

    elif config.MODEL =="D":
        print(" creation of architecture D")
        model = VGG16_2(in_channels=config.IN_CHANNELS, num_classes=config.NUM_CLASSES).to(device=config.DEVICE)
        optimizer = optim.SGD(model.parameters(), momentum=0.9, lr=1e-2, weight_decay=5e-4)


    #getting train and test loaders
    train_loader, test_loader = get_loaders()



    #loading model in case we want to continue training
    if config.LOAD_MODEL:
        load_checkpoint(model=model, optimizer=optimizer, lr=config.LEARNING_RATE)

    writer = SummaryWriter(config.LOGS_PATH)
    tensorboard_step = 0
    old_accuracy = 0

    for epoch in range(config.NUM_EPOCHS):
        print("Epoch: ", epoch)
        train_loss = train_fn(model, loader=train_loader, optimizer=optimizer)
        test_loss, accuracy = test(model=model, test_loader=test_loader)

        plot_to_tensorboard(writer=writer, train_loss=train_loss, test_loss=test_loss, test_accuracy=accuracy,
                            tensorboard_step=tensorboard_step)

        tensorboard_step += 1

        print("accuracy = ", accuracy, " old_accurcy =", old_accuracy)
        if accuracy > old_accuracy:
            file_name = config.MODEL +".pth.tar"
            save_checkpoint(model=model, optimizer=optimizer, file_name=file_name)
            old_accuracy = accuracy

def train_fn(model, loader, optimizer):

    loop = tqdm(loader, leave=True)
    model.train()
    train_loss = 0
    for batch_idx, (data, targets) in enumerate(loop):
        data = data.to(device=config.DEVICE)
        targets = targets.to(device=config.DEVICE)

        optimizer.zero_grad()
        predictions = model(data)
        loss = nn.CrossEntropyLoss()(predictions, targets)

        loss.backward()
        #torch.nn.utils.clip_grad_norm_(model.parameters(), 1)
        optimizer.step()

        train_loss += loss.item()
        loop.set_postfix(train_loss=loss.item())

    return train_loss/len(loader.dataset)


def test(model, test_loader):
    model.eval()
    test_loss = 0
    correct = 0

    with torch.no_grad():
        loop = tqdm(test_loader, leave=True)
        for _, (data, target) in enumerate(loop):
            data, target = data.to(config.DEVICE), target.to(config.DEVICE)
            output = model(data)

            loss = nn.CrossEntropyLoss()(output, target)
            test_loss += loss.item()

            # output shape: [batch_size, num_classes]
            _, predicted = output.max(1)
            # predicted shape: [batch_size, 1]

            correct += predicted.eq(target).sum().item()

        test_loss /= len(test_loader.dataset)
        accuracy = 100. * correct / len(test_loader.dataset)

        loop.set_postfix(test_loss=test_loss, accuracy=accuracy)
        return test_loss, accuracy