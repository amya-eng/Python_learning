import numpy as np
import pickle


def load_mnist_data(kind):
    labels_path = '%s-labels.idx1-ubyte' % kind
    images_path = '%s-images.idx3-ubyte' % kind  # >表示字节顺序是big-endian，也就是网络序，I表示4字节无符号整数。
    with open(labels_path, 'rb') as lbpath:
        labels = np.fromfile(lbpath, dtype=np.uint8, offset=8)
    with open(images_path, 'rb') as imgpath:
        images = np.fromfile(imgpath, dtype=np.uint8, offset=16).reshape(len(labels), 784)
    return images / 255, np.eye(10)[labels]


def leaky_relu(z):
    return np.where(z > 0, z, z * 0.01)  # 满足 z > 0, 则输出z， 否则输出z * 0.01


def leaky_relu_prime(z):
    z_ = np.copy(z)
    z_[z > 0] = 1
    z_[z < 0] = 0.01
    z_[z == 0] = 0.5
    return z_


def mean_squared_loss(z, y_true):

    y_predict = leaky_relu(z)
    loss = np.mean(np.mean(np.square(y_predict - y_true), axis=-1))  # 损失函数值
    dy = 2 * (y_predict - y_true) * leaky_relu_prime(z) / y_true.shape[1]  # y_true.shape[1]表示数据总数
    return loss, dy


class MLP_Net:
    def __init__(self, sizes, loss_type='mse'):  # 默认使用均方差损失函数
        self.sizes = sizes
        self.num_layers = len(sizes)  # sizes 是一个列表，元素表示每一层含有地神经元个数
        weights_scale = 0.01
        self.weights = [np.random.randn(ch1, ch2) * weights_scale for ch1, ch2 in zip(sizes[:-1], sizes[1:])]
        self.biases = [np.random.randn(1, ch) * weights_scale for ch in sizes[1:]]
        self.X = None
        self.Z = None
        self.loss_type = loss_type
        self.training = True

    def forward(self, x):                               # 使得之后的每一层都仿射化
        self.X = [x]  # 存放每一层的输出
        self.Z = []  # 存放每一层的输入
        for layer_idx, (b, w) in enumerate(zip(self.biases, self.weights)):
            z = np.dot(x, w) + b
            x = leaky_relu(z)
            self.X.append(x)
            self.Z.append(z)
        return self.X[-1]

    def backward(self, y):
        dw = [np.zeros(w.shape) for w in self.weights]
        db = [np.zeros(b.shape) for b in self.biases]
        loss, delta = mean_squared_loss(self.Z[-1], y)
        batch_size = len(y)
        for num in range(self.num_layers - 2, -1, -1):
            x = self.X[num]
            db[num] = np.sum(delta, axis=0) / batch_size
            dw[num] = np.dot(x.T, delta) / batch_size

            if num > 0:
                delta = np.dot(delta, self.weights[num].T) * leaky_relu_prime(self.Z[num - 1])
        return dw, db

    def update_para(self, dw, db):
        self.weights = [w - 0.4 * nabla for w, nabla in zip(self.weights, dw)]
        self.biases = [b - 0.4 * nabla for b, nabla in zip(self.biases, db)]


def plot_trainning(order1, order2, img_name):
    with open(order1, 'rb') as f1, open(order2, 'rb') as f2:
        accs1 = pickle.load(f1)
        accs2 = pickle.load(f2)

    import matplotlib.pyplot as plt
    plt.figure()
    # x = [str(i) for i in range(1, len(accs1) + 1)]
    x = [i for i in range(1, len(accs1) + 1)]
    plt.plot(x, accs1, label=order1)
    plt.plot(x, accs2, label=order2)
    plt.legend()
    # plt.ylim((0, 1))
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.savefig(img_name)


def plot_single_training(order, img_name='best_acc.png'):
    with open(order, 'rb') as f1:
        accs = pickle.load(f1)
    import matplotlib.pyplot as plt
    plt.figure()
    x = [i for i in range(1, len(accs) + 1)]
    plt.plot(x, accs)
    # plt.legend()
    # plt.ylim((0, 1))
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.savefig(img_name)


def train(net, train_images, train_labels, test_images, test_labels, epochs=1000, batch_size=128, orders='first'):
    n = len(train_images)
    accs = []
    for epoch in range(epochs):
        net.training = True
        for batch_index in range(0, n, batch_size):
            lower_range = batch_index
            upper_range = batch_index + batch_size
            if upper_range > n:
                upper_range = n
            train_x = train_images[lower_range: upper_range, :]
            train_y = train_labels[lower_range: upper_range]
            net.forward(train_x)
            dw, db = net.backward(train_y)
            net.update_para(dw, db)
        acc = evaluate(net, test_images, test_labels)
        accs.append(acc / 10000.0)
        print('Epoch {0}: {1}'.format(epoch, acc / 10000.0))
    plot_single_training(orders)


def evaluate(net, test_images, test_labels):

    net.training = False
    result = []
    n = len(test_images)
    for batch_indx in range(0, n, 128):
        lower_range = batch_indx
        upper_range = batch_indx + 128
        if upper_range > n:
            upper_range = n
        test_x = test_images[lower_range: upper_range, :]
        result.extend(np.argmax(net.forward(test_x), axis=1))
    correct = sum(int(pred == y) for pred, y in zip(result, test_labels))
    return correct


def main():
    train_images, train_labels = load_mnist_data(kind='train')
    test_images, test_labels = load_mnist_data(kind='t10k')
    test_labels = np.argmax(test_labels, axis=1)  # shape=(10000,)
    net = MLP_Net([784, 1024, 64, 10], 'mse')  # [输入层，隐藏层1， 隐藏层2， 输出层]
    orders1 = 'no_regular'
    train(net, train_images, train_labels, test_images, test_labels, epochs=10, orders=orders1, batch_size=64)


if __name__ == '__main__':
    np.random.seed(0)  # 实验结果可复现
    main()