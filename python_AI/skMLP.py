from sklearn.neural_network import MLPClassifier
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

digits = load_digits()
x = digits['data']
y = digits['target']

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3)
clf = MLPClassifier(solver='adam', alpha=1e-5, hidden_layer_sizes=(1024, 64), random_state=1, max_iter=1000)
clf.fit(x_train, y_train)
print(clf.score(x_test, y_test))
