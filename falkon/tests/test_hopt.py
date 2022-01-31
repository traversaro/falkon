import pytest
import torch
from falkon import FalkonOptions
from falkon.hopt.objectives import (SGPR, CompReg, GCV, HoldOut, LOOCV, NystromCompReg,
                                    StochasticNystromCompReg)
from falkon.kernels import GaussianKernel


def init_model(model_cls, centers_init, sigma_init, penalty_init, opt_centers, opt_sigma, opt_penalty):
    if model_cls == HoldOut:
        return HoldOut(centers_init, sigma_init, penalty_init, opt_centers, opt_sigma, opt_penalty,
                       val_pct=0.8, per_iter_split=False)
    return model_cls(centers_init, sigma_init, penalty_init, opt_centers, opt_sigma, opt_penalty)


@pytest.mark.parametrize("model_cls", [CompReg])#NystromCompReg, CompReg, SGPR, GCV, LOOCV, HoldOut])
def test_exact_objectives(model_cls):
    # Generate some synthetic data
    torch.manual_seed(12)
    n = 1000
    num_centers = 100
    X = torch.randn((n, 10))
    w = torch.arange(X.shape[1], dtype=torch.float32).reshape(-1, 1)
    Y = X @ w + torch.randn((X.shape[0], 1)) * 0.3  # 10% noise

    num_train = int(X.shape[0] * 0.8)
    X_train, Y_train = X[:num_train], Y[:num_train]
    X_test, Y_test = X[num_train:], Y[num_train:]
    # Standardize X, Y
    x_mean, x_std = torch.mean(X_train, dim=0, keepdim=True), torch.std(X_train, dim=0, keepdim=True)
    y_mean, y_std = torch.mean(Y_train, dim=0, keepdim=True), torch.std(Y_train, dim=0, keepdim=True)
    X_train = (X_train - x_mean) / x_std
    X_test = (X_test - x_mean) / x_std
    Y_train = (Y_train - y_mean) / y_std
    Y_test = (Y_test - y_mean) / y_std

    sigma_init = torch.tensor([5.0] * X_train.shape[1], dtype=torch.float32)
    penalty_init = torch.tensor(1e-5, dtype=torch.float32)
    centers_init = X_train[:num_centers].clone()

    # model = init_model(model_cls, centers_init, sigma_init, penalty_init, True, True, True)
    kernel = GaussianKernel(sigma_init.requires_grad_())
    model = CompReg(kernel, centers_init, penalty_init, True, True)
    opt_hp = torch.optim.Adam(model.parameters(), lr=0.1)

    print("params")
    print([p.shape for p in model.parameters()])
    print([p.dtype for p in model.parameters()])

    for epoch in range(50):
        opt_hp.zero_grad()
        loss = model(X_train, Y_train)
        print("Loss", loss)
        loss.backward()
        opt_hp.step()
    ts_err = torch.mean((model.predict(X_test) - Y_test)**2)
    print("Model %s obtains %.4f error" % (model_cls, ts_err))
    # assert ts_err < 300


def test_stoch_objectives():
    # Generate some synthetic data
    torch.manual_seed(12)
    n = 1000
    num_centers = 100
    X = torch.randn((n, 10))
    w = torch.arange(X.shape[1], dtype=torch.float32).reshape(-1, 1)
    Y = X @ w + torch.randn((X.shape[0], 1)) * 0.3  # 10% noise

    num_train = int(X.shape[0] * 0.8)
    X_train, Y_train = X[:num_train], Y[:num_train]
    X_test, Y_test = X[num_train:], Y[num_train:]
    # Standardize X, Y
    x_mean, x_std = torch.mean(X_train, dim=0, keepdim=True), torch.std(X_train, dim=0, keepdim=True)
    y_mean, y_std = torch.mean(Y_train, dim=0, keepdim=True), torch.std(Y_train, dim=0, keepdim=True)
    X_train = (X_train - x_mean) / x_std
    X_test = (X_test - x_mean) / x_std
    Y_train = (Y_train - y_mean) / y_std
    Y_test = (Y_test - y_mean) / y_std

    sigma_init = torch.tensor([5.0] * X_train.shape[1], dtype=torch.float32)
    penalty_init = torch.tensor(1e-5, dtype=torch.float32)
    centers_init = X_train[:num_centers].clone()
    flk_opt = FalkonOptions(use_cpu=True, keops_active="no")

    model = StochasticNystromCompReg(centers_init, sigma_init, penalty_init, True, True, True,
                                     flk_opt=flk_opt, flk_maxiter=10, num_trace_est=10)
    opt_hp = torch.optim.Adam(model.parameters(), lr=0.1)

    for epoch in range(50):
        opt_hp.zero_grad()
        loss = model(X_train, Y_train)
        loss.backward()
        opt_hp.step()
    ts_err = torch.mean((model.predict(X_test) - Y_test)**2)
    print("Model %s obtains %.4f error" % (model.__class__, ts_err))
    # assert ts_err < 300