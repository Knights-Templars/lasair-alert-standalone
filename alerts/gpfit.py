import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel, Matern


def fit_gp(mjd, mag, mag_err):

    X = np.array(mjd).reshape(-1, 1)
    X = (X - X.min()) / (X.max() - X.min())
    y = np.array(mag)

    noise = np.array(mag_err)**2

    kernel = ConstantKernel(1.0) * \
            Matern(length_scale=0.1,
                   nu=1.5)
    
    gp = GaussianProcessRegressor(
        kernel=kernel,
        alpha=noise,      
        normalize_y=True,
        n_restarts_optimizer=5
    )

    gp.fit(X, y)

    X_pred = np.linspace(X.min(), X.max(), 500).reshape(-1, 1)

    y_pred, sigma = gp.predict(X_pred, return_std=True)

    return X_pred.ravel(), y_pred, sigma








    
