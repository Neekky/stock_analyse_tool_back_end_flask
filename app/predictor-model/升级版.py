# 导入必要的库
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.callbacks import ReduceLROnPlateau

import matplotlib.pyplot as plt
import seaborn as sns
import datetime

# 设置中文字体为 SimHei
plt.rcParams['font.sans-serif'] = ['PingFang SC']  # 可以替换为其他支持中文的字体，如 'Microsoft YaHei'
plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题

# 设置绘图风格
sns.set_theme(style='whitegrid')

# 读取数据
# 假设数据存储在 'stock_data.csv' 文件中，包含 'Date', '涨家数', '跌家数', '涨停家数', '跌停家数' 等列
data = pd.read_csv('涨跌趋势.csv', parse_dates=['日期'])

# 按日期排序
data.sort_values('日期', inplace=True)

# 选择特征和目标
# 这里假设我们用过去N天的所有特征来预测下一天的涨家数和跌家数
feature_cols = ['上涨家数', '下跌家数', '涨停数', '跌停数']
target_cols = ['上涨家数', '下跌家数']

# 填补缺失值（如果有）
data.ffill(inplace=True)

# 将数据转换为numpy数组
data_values = data[feature_cols].values

# 标准化特征
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data_values)

# 定义序列长度（使用过去N天的数据）
sequence_length = 30  # 可以根据实际情况调整

# 创建序列数据
def create_sequences(data, seq_length, target_cols_indices):
    X = []
    y = []
    for i in range(seq_length, len(data)):
        X.append(data[i-seq_length:i])
        y.append(data[i][target_cols_indices])
    return np.array(X), np.array(y)

# 目标列的索引
target_cols_indices = [feature_cols.index(col) for col in target_cols]

X, y = create_sequences(scaled_data, sequence_length, target_cols_indices)

# 将数据拆分为训练集和测试集
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

print(f"训练集大小: {X_train.shape}")
print(f"测试集大小: {X_test.shape}")

# 构建LSTM模型
model = Sequential()

# 第一层LSTM
model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(Dropout(0.2))

# 第二层LSTM
model.add(LSTM(units=50, return_sequences=False))
model.add(Dropout(0.2))

# 输出层
model.add(Dense(units=y_train.shape[1]))

# 编译模型
model.compile(optimizer='adam', loss='mean_squared_error')

# 模型摘要
model.summary()

# 早停机制：使用EarlyStopping回调函数，根据验证集的损失提前停止训练，避免过拟合。
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# 学习率调整：使用学习率调度器（如ReduceLROnPlateau）在训练过程中动态调整学习率，提高训练效率。
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.001)

# 训练模型
history = model.fit(X_train, y_train,
                    epochs=100,
                    batch_size=32,
                    validation_data=(X_test, y_test),
                    callbacks=[early_stop, reduce_lr],
                    verbose=1)

# 绘制训练过程中的损失变化
plt.figure(figsize=(12,6))
plt.plot(history.history['loss'], label='xunlian训练损失')
plt.plot(history.history['val_loss'], label='yanzheng验证损失')
plt.title('sunshi损失函数变化')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()

# 进行预测
y_pred = model.predict(X_test)

# 反标准化预测值和真实值
# 由于我们只预测了部分特征，因此需要进行逆变换时只针对目标列
# 创建一个与y_pred和y_test相同形状的数组，用于逆变换
def inverse_transform(scaled_data, scaler, target_cols_indices):
    dummy = np.zeros((scaled_data.shape[0], scaler.n_features_in_))
    dummy[:, target_cols_indices] = scaled_data
    inversed = scaler.inverse_transform(dummy)
    return inversed[:, target_cols_indices]

y_pred_inv = inverse_transform(y_pred, scaler, target_cols_indices)
y_test_inv = inverse_transform(y_test, scaler, target_cols_indices)

# 计算评估指标
mse = mean_squared_error(y_test_inv, y_pred_inv)
mae = mean_absolute_error(y_test_inv, y_pred_inv)
r2 = r2_score(y_test_inv, y_pred_inv)

print(f"均方误差(MSE): {mse}")
print(f"平均绝对误差(MAE): {mae}")
print(f"R²得分: {r2}")

# 可视化预测结果
plt.figure(figsize=(14,7))

# 以涨家数为例
plt.subplot(2,1,1)
plt.plot(data['日期'][-len(y_test_inv):], y_test_inv[:,0], label='zhenshi真实涨家数')
plt.plot(data['日期'][-len(y_test_inv):], y_pred_inv[:,0], label='yuce预测涨家数')
plt.title('count涨家数预测')
plt.xlabel('日期')
plt.ylabel('涨家数')
plt.legend()

# 以跌家数为例
plt.subplot(2,1,2)
plt.plot(data['日期'][-len(y_test_inv):], y_test_inv[:,1], label='zhenshi真实跌家数')
plt.plot(data['日期'][-len(y_test_inv):], y_pred_inv[:,1], label='yuce预测跌家数')
plt.title('跌家数预测')
plt.xlabel('日期')
plt.ylabel('跌家数')
plt.legend()

plt.tight_layout()
plt.show()

# 预测下一天的涨跌家数
def predict_next_day(model, data, scaler, sequence_length, target_cols_indices):
    last_sequence = data[-sequence_length:]
    last_sequence_scaled = scaler.transform(last_sequence)
    last_sequence_scaled = np.expand_dims(last_sequence_scaled, axis=0)  # 增加batch维度
    prediction_scaled = model.predict(last_sequence_scaled)
    prediction_inv = inverse_transform(prediction_scaled, scaler, target_cols_indices)
    return prediction_inv

# 获取最近的sequence_length天的数据
recent_data = data[feature_cols].tail(sequence_length).values
prediction = predict_next_day(model, recent_data, scaler, sequence_length, target_cols_indices)
print(f"预测下一天的涨家数和跌家数: {prediction}")