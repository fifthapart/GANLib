from GANLib import ProgGAN
from GANLib import plotter

from keras.datasets import mnist, fashion_mnist, cifar10
from keras.layers import Input, Dense, Reshape, Flatten, Dropout, concatenate, RepeatVector, UpSampling2D
from keras.layers import BatchNormalization, Activation, Embedding, ZeroPadding2D, AveragePooling2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Conv2D
from keras.models import Model
from keras.optimizers import Adam, RMSprop, Nadam

import matplotlib.pyplot as plt
import numpy as np


def build_generator(self):
    input_layer = Input(shape=(self.latent_dim,))
    layer = RepeatVector(16)(input_layer)
    layer = Reshape((4, 4, self.latent_dim))(layer)
    
    layer = Conv2D(self.latent_dim, (4,4), padding='same', weights = self.genr_head_weights, name = 'genr_head')(layer)
    layer = LeakyReLU(alpha=0.2)(layer) 
    
    #Growing layers
    for i in range(self.layers):
        layer = UpSampling2D(2)(layer)
        layer = Conv2D(64, (3,3), padding='same', weights = self.genr_weights[i], name = 'genr_layer_'+str(i))(layer)
        layer = LeakyReLU(alpha=0.2)(layer) 
    
    
    layer = Conv2D(3, (1,1))(layer)
    return Model(input_layer, layer)
    
def build_discriminator(self):
    input_layer = Input(shape=self.inp_shape)
    layer = input_layer
    
    layer = Conv2D(64, (1,1))(layer)
    layer = LeakyReLU(alpha=0.2)(layer) 
    
    #Growing layers
    for i in range(self.layers):
        layer = Conv2D(64, (3,3), padding='same', weights = self.disc_weights[i], name = 'disc_layer_'+str(i))(layer)
        layer = LeakyReLU(alpha=0.2)(layer)
        layer = AveragePooling2D(2)(layer)
    
    layer = Conv2D(self.latent_dim, (4,4), padding='valid', weights = self.disc_head_weights, name = 'disc_head')(layer)
    layer = LeakyReLU(alpha=0.2)(layer) 
    layer = Flatten()(layer)
    layer = Dense(1, activation=self.disc_activation)(layer)
    
    return Model(input_layer, layer)


       
noise_dim = 100    

def sample_images(gen, file):
    r, c = 5, 5
    
    noise = np.random.uniform(-1, 1, (r * c, noise_dim))

    gen_imgs = gen.predict([noise])

    # Rescale images 0 - 1
    gen_imgs = 0.5 * gen_imgs + 0.5
    gen_imgs = np.clip(gen_imgs,0,1)
    
    fig, axs = plt.subplots(r, c)
    cnt = 0
    for i in range(r):
        for j in range(c):
            if gen_imgs.shape[-1] == 1: 
                axs[i,j].imshow(gen_imgs[cnt,:,:,0], cmap='gray')
            else:
                axs[i,j].imshow(gen_imgs[cnt,:,:])
            axs[i,j].axis('off')
            cnt += 1
    fig.savefig(file) #% epoch
    plt.close()   
    
    
img_path = 'ProgGAN'
mode = 'vanilla'
    
# Load the dataset
(X_train, labels), (_, _) = cifar10.load_data()

indx = np.where(labels == 1)[0]
X_train = X_train[indx]

# Configure input
X_train = (X_train.astype(np.float32) - 127.5) / 127.5

if len(X_train.shape)<4:
    X_train = np.expand_dims(X_train, axis=3)

#Run GAN for 20000 iterations
gan = ProgGAN(X_train.shape[1:], noise_dim, mode = mode)
gan.build_generator = lambda self=gan: build_generator(self)
gan.build_discriminator = lambda self=gan: build_discriminator(self)
gan.build_models()

def callback():
    path = 'images/'+img_path+'/conv_'+mode
    sample_images(gan.generator, path+'.png')
    plotter.save_hist_image(gan.history, path+'_hist.png')
    
gan.train(X_train, epochs=20000, grow_epochs = [1000, 3000, 8000], batch_size=64, checkpoint_callback = callback, validation_split = 0.1)    