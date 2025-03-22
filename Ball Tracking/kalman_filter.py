import numpy as np

class KalmanFilter:

    def __init__(self, dt, process_variance, measurement_variance):
        self.dim_x = 6

        self.dim_z = 4

        self.A = np.array([
            [1, 0, 0, 0, dt, 0],
            [0, 1, 0, 0, 0, dt],
            [0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])
        
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0]
        ])
        
        self.Q = np.eye(self.dim_x)

        self.R = np.eye(self.dim_z) * measurement_variance
        self.x = np.zeros((self.dim_x, 1))
        self.P = np.eye(self.dim_x) * 1000 
        self.initialized = False
    
    def initialize(self, initial_pos):

        self.x = np.array([[initial_pos[0]], [initial_pos[1]], [initial_pos[2]], [initial_pos[3]], [0], [0]])
        self.initialized = True
    
    def predict(self):

        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q
        return self.x[:self.dim_z].flatten().astype(np.int32).tolist()
    
    def update(self, measurement):

        measurement = np.array(measurement)
        if not self.initialized:
            self.initialize(measurement)
            return self.x[:self.dim_z].flatten()
        
        z = measurement.reshape((self.dim_z, 1))
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(self.dim_x) - K @ self.H) @ self.P
        
        return self.x[:self.dim_z].flatten().astype(np.int32).tolist()