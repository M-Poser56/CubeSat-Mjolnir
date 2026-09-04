"""
Reaction wheel attitude control.

Quaternion convention: scalar-first, [q0, q1, q2, q3] with q0 the scalar
part. All quaternions represent the body-frame orientation relative to
the inertial/reference frame and are kept unit-norm.

Three reaction wheels are assumed mounted with spin axes along the body
x, y, z axes (wheel_axes defaults to the identity matrix). Motor driver
code (translating a commanded wheel speed/torque into actual PWM/I2C
output) is out of scope here -- this module only produces the target
wheel torques and speeds for that layer to track.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Quaternion math
# ---------------------------------------------------------------------------

def quat_normalize(q: np.ndarray) -> np.ndarray:
    return q / np.linalg.norm(q)


def quat_conjugate(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]])


def quat_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def quat_error(q_current: np.ndarray, q_target: np.ndarray) -> np.ndarray:
    """Rotation from q_target to q_current, expressed in the body frame."""
    q_e = quat_multiply(quat_conjugate(q_target), q_current)
    # Keep the scalar part positive so we always take the shortest path
    # (q and -q represent the same rotation, but their error dynamics
    # near q_e0 = -1 would otherwise spin the wrong way).
    if q_e[0] < 0:
        q_e = -q_e
    return q_e


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class ReactionWheelController:
    def __init__(
        self,
        kp: float,
        kd: float,
        wheel_inertia: np.ndarray,
        max_wheel_speed: float,
        max_wheel_torque: float,
        wheel_axes: np.ndarray = np.eye(3),
    ):
        """
        kp, kd:            PD gains on quaternion error / body rate.
        wheel_inertia:      (3,) spin-axis inertia of each wheel, kg*m^2.
        max_wheel_speed:    saturation limit, rad/s.
        max_wheel_torque:   saturation limit, N*m.
        wheel_axes:         (3,3) matrix whose columns are each wheel's
                             spin axis in the body frame (unit vectors).
                             Identity => wheels aligned with body x/y/z.
        """
        self.kp = kp
        self.kd = kd
        self.wheel_inertia = np.asarray(wheel_inertia, dtype=float)
        self.max_wheel_speed = max_wheel_speed
        self.max_wheel_torque = max_wheel_torque
        self.wheel_axes = np.asarray(wheel_axes, dtype=float)
        self.wheel_axes_inv = np.linalg.pinv(self.wheel_axes)

        self.wheel_speeds = np.zeros(3)  # rad/s, current commanded speed per wheel

    def compute_body_torque(
        self,
        q_current: np.ndarray,
        q_target: np.ndarray,
        omega_body: np.ndarray,
        omega_target: np.ndarray = np.zeros(3),
    ) -> np.ndarray:
        """PD control law on quaternion error and body rate error, returns
        the desired net torque on the spacecraft body, N*m."""
        q_e = quat_error(quat_normalize(q_current), quat_normalize(q_target))
        omega_error = omega_body - omega_target
        return -self.kp * q_e[1:] - self.kd * omega_error

    def allocate_wheel_torques(self, body_torque: np.ndarray) -> np.ndarray:
        """Map a desired body torque to per-wheel torques. Newton's third
        law: spinning a wheel up applies the opposite torque to the body,
        so the wheels must produce -body_torque along their spin axes."""
        wheel_torques = self.wheel_axes_inv @ (-body_torque)
        return np.clip(wheel_torques, -self.max_wheel_torque, self.max_wheel_torque)

    def step(
        self,
        q_current: np.ndarray,
        omega_body: np.ndarray,
        q_target: np.ndarray,
        omega_target: np.ndarray,
        dt: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Run one control cycle. Returns (wheel_torques, wheel_speeds).
        Integrates and saturates the internal wheel speed state; the motor
        driver layer is responsible for actually tracking wheel_speeds."""
        body_torque = self.compute_body_torque(q_current, q_target, omega_body, omega_target)
        wheel_torques = self.allocate_wheel_torques(body_torque)

        wheel_accel = wheel_torques / self.wheel_inertia
        self.wheel_speeds = np.clip(
            self.wheel_speeds + wheel_accel * dt,
            -self.max_wheel_speed,
            self.max_wheel_speed,
        )
        return wheel_torques, self.wheel_speeds


if __name__ == "__main__":
    controller = ReactionWheelController(
        kp=0.8,
        kd=0.4,
        wheel_inertia=np.array([1e-4, 1e-4, 1e-4]),
        max_wheel_speed=600.0,
        max_wheel_torque=0.01,
    )

    q_current = np.array([1.0, 0.0, 0.0, 0.0])  # identity orientation
    q_target = quat_normalize(np.array([0.92, 0.0, 0.0, 0.38]))  # ~45 deg about z
    omega_body = np.zeros(3)
    omega_target = np.zeros(3)
    dt = 0.05

    for step_num in range(10):
        wheel_torques, wheel_speeds = controller.step(
            q_current, omega_body, q_target, omega_target, dt
        )
        print(f"step {step_num}: wheel_torques={wheel_torques}, wheel_speeds={wheel_speeds}")
