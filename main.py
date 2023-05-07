import os
import torch
from torch import nn
import torch.nn.functional as F
import torchvision
from torch.utils.data import DataLoader

device = 'cuda' if torch.cuda.is_available() else 'cpu'

class VAE(nn.Module):
    def __init__(self,in_dim=784, h_dim=256, z_dim=2):
        super(VAE, self).__init__()

        self.fc1 = nn.Linear(784, 256)
        self.fc2_mu = nn.Linear(256, 2)
        self.fc2_log_std = nn.Linear(256, 2)
        self.fc3 = nn.Linear(2, 256)
        self.fc4 = nn.Linear(256, 784)

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        mu = self.fc2_mu(h1)
        log_std = self.fc2_log_std(h1)
        return mu, log_std

    def decode(self, z):
        h3 = F.relu(self.fc3(z))
        recon = torch.sigmoid(self.fc4(h3))
        return recon

    def reparametrize(self, mu, log_std):
        std = torch.exp(log_std)
        eps = torch.randn_like(std)
        z = mu + eps * std
        return z

    def forward(self, x):
        mu, log_std = self.encode(x)
        z = self.reparametrize(mu, log_std)
        recon = self.decode(z)
        return recon, mu, log_std

    def loss_function(self, recon, x, mu, log_std):
        recon_loss = F.mse_loss(recon, x, reduction="sum") 
        kl_loss = -0.5 * (1 + 2*log_std - mu.pow(2) - torch.exp(2*log_std))
        kl_loss = torch.sum(kl_loss)
        loss = recon_loss + kl_loss
        return loss

def to_img(x):
    x = x.clamp(0, 1)
    imgs = x.reshape(x.shape[0], 1, 28, 28)
    return imgs

def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    epochs = 100
    batch_size = 100

    recon = None
    img = None

    
    make_dir("./img/vae")
    make_dir("./model_weights/vae")

    train_data = torchvision.datasets.MNIST(
        root='./data',
        train=True,
        transform=torchvision.transforms.ToTensor(),
        download=True
    )

    data_loader = DataLoader(train_data, batch_size=100, shuffle=True)

    vae = VAE().to(device)

    optimizer = torch.optim.Adam(vae.parameters(), lr=1e-3)

    for epoch in range(100):
        train_loss = 0
        i = 0
        for batch_id, data in enumerate(data_loader):
            img, _ = data
            # print(img.shape)
            inputs = img.reshape(img.shape[0], -1).to(device)
            # print(inputs.shape)
            recon, mu, log_std = vae(inputs)
            loss = vae.loss_function(recon, inputs, mu, log_std)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            i += 1

            if batch_id % 100 == 0:
                print("Epoch[{}/{}], Batch[{}/{}], batch_loss:{:.6f}".format(
                    epoch+1, epochs, batch_id+1, len(data_loader), loss.item()))

        print("======>epoch:{},\t epoch_average_batch_loss:{:.6f}============".format(epoch+1, train_loss/i), "\n")

        # save imgs
        if epoch % 10 == 0:
            imgs = to_img(recon.detach())
            print(recon.shape)
            path = "./img/vae/epoch{}.png".format(epoch+1)
            torchvision.utils.save_image(imgs, path, nrow=10)
            print("save:", path, "\n")
            g = (torch.tensor([(x, y) for y in range(20) for x in range(20)]).to(device,dtype=torch.float32).reshape((400, 2)) - 10)/2
            linear_recons = vae.decode(g)
            linear_imgs = to_img(linear_recons.detach())
            linear_path = "./img/vae/linear_epoch{}.png".format(epoch+1)
            torchvision.utils.save_image(linear_imgs, linear_path, nrow=20)
            print("save:", linear_path, "\n")

    torchvision.utils.save_image(img, "./img/vae/raw.png", nrow=10)
    print("save raw image:./img/vae/raw/png", "\n")

    # save val model
    torch.save(vae, "./model_weights/vae/vae_weights.pth")
