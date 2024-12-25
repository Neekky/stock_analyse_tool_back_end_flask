import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 读取数据
data = pd.read_csv('涨跌趋势.csv')

# 特征工程：创建移动平均值等特征
data['5_day_up_avg'] = data['上涨家数'].rolling(window=5).mean().shift(1)
data['5_day_down_avg'] = data['下跌家数'].rolling(window=5).mean().shift(1)

# 删除缺失值
data.dropna(inplace=True)

# 创建标签
data['label'] = (data['上涨家数'] > data['下跌家数']).astype(int)

# 特征和标签
X = data[['5_day_up_avg', '5_day_down_avg']]
y = data['label']

# 数据分割
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 模型定义和训练
parameters = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10]
}
clf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(clf, parameters, cv=5, n_jobs=-1, verbose=1)
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_
print(f'最佳模型参数: {grid_search.best_params_}')

# 使用最佳模型进行预测
y_pred = best_model.predict(X_test)

# 模型评估
accuracy = accuracy_score(y_test, y_pred)
print(f'模型准确性: {accuracy:.2f}')
print(classification_report(y_test, y_pred))

# 预测未来数据
future_data = data.tail(5)
future_data = future_data[['5_day_up_avg', '5_day_down_avg']]

predicted_label = best_model.predict(future_data)
print('未来数据预测标签:', predicted_label)
