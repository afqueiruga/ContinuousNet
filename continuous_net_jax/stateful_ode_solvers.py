"""These functions are designed for mutatable functions.

A Flax model functionally emits both the mutated variables:

F(p, x, mutable=False) = dx/dt
F(p, x, mutable=True) = p', dx/dt

These schemes are aware of that statefulness:

"""

import jax
import jax.numpy as jnp
import numpy as onp

import flax

from .continuous_types import *

# Integrators
# Rigorously, one step only evaluates f on the open set [t0, t0+Dt). We substract
# this eps to keep evaluations of params_of_t inside of that interval to align
# with domains.
DT_OPEN_SET_EPS = 1.0e-5


def Euler(params_of_t: ContinuousParameters,
          x: ArrayType,
          t0: float = 0,
          f: RateEquation = None,
          Dt: float = 1.0) -> ArrayType:
    """Forward Euler, O(Dt)."""
    state1, k1 = f(params_of_t(t0), x)
    return state1, x + Dt * k1


def Midpoint(params_of_t: ContinuousParameters,
             x: ArrayType,
             t0: float = 0,
             f=None,
             Dt: float = 1.0) -> ArrayType:
    """Explicit Midpoint, a two stage Runge Kutta, O(Dt^2)."""
    state1, k1 = f(params_of_t(t0), x)
    x1 = x + 0.5 * Dt * k1  # t = 1/2
    state2, k2 = f(params_of_t(t0 + 0.5 * Dt), x1)
    return state2, x + Dt * k2


def RK4(params_of_t: ContinuousParameters,
        x: ArrayType,
        t0: float = 0,
        f=None,
        Dt: float = 1.0):
    """The 'classic' RK4, a four stage Runge Kutta, O(Dt^4)."""
    state1, k1 = f(params_of_t(t0), x)  # t = 0+ (inside of domain)
    x1 = x + 0.5 * Dt * k1
    state2, k2 = f(params_of_t(t0 + 0.5 * Dt), x1)  # t = 1/2
    x2 = x + 0.5 * Dt * k2
    state3, k3 = f(params_of_t(t0 + 0.5 * Dt), x2)  # t = 1/2
    x3 = x + Dt * k3
    state4, k4 = f(params_of_t(t0 + Dt - DT_OPEN_SET_EPS), x3)  # t = 1- (inside domain)
    return x + Dt * (1.0 / 6.0 * k1 + 1.0 / 3.0 * k2 + 1.0 / 3.0 * k3 +
                     1.0 / 6.0 * k4)


def RK4_38(params_of_t: ContinuousParameters,
        x: ArrayType,
        t0: float = 0,
        f=None,
        Dt: float = 1.0):
    """The 3/8s RK4, a four stage Runge Kutta, O(Dt^4)."""
    state1, k1 = f(params_of_t(t0), x)  # t = 0+ (inside of domain)
    x1 = x + 1.0/3.0 * Dt * k1
    state2, k2 = f(params_of_t(t0 + 1.0/3.0 * Dt), x1)  # t = 1/3
    x2 = x + Dt * (-1.0/3.0 * k1 +  1.0 * k2)
    state3, k3 = f(params_of_t(t0 + 2.0/3.0 * Dt), x2)  # t = 2/2
    x3 = x + Dt *( k1 - k2 + k3)
    state4, k4 = f(params_of_t(t0 + Dt - DT_OPEN_SET_EPS), x3)  # t = 1-
    xf = x + Dt * (1.0 / 8.0 * k1 + 3.0 / 8.0 * k2 + 3.0 / 8.0 * k3 +
                     1.0 / 8.0 * k4)
    return state4, xf


SCHEME_TABLE = {
    'Euler': Euler,
    'Midpoint': Midpoint,
    'RK4': RK4,
    'RK4_38': RK4_38,
}


def StateOdeIntegrateFast(params_of_t: ContinuousParameters,
                             x: ArrayType,
                             f: RateEquation,
                             scheme: IntegrationScheme = Euler,
                             n_step: int = 10) -> ArrayType:
    dt = 1.0 / n_step
    for t in onp.linspace(0, 1, n_step):
        state, x = scheme(params_of_t, x, t, f, dt)
    return x


def StateOdeIntegrateWithPoints(params_of_t: ContinuousParameters,
                           x: ArrayType,
                           f: RateEquation,
                           scheme: IntegrationScheme = Euler,
                           n_step: int = 10) -> List[ArrayType]:
    dt = 1.0 / n_step
    xs = [onp.array(x)]
    for t in onp.linspace(0, 1, n_step):
        state, x = scheme(params_of_t, x, t, f, dt)
        xs.append(onp.array(x))
    return xs