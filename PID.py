import time


class PIDFController:
    def __init__(self, kp=0, ki=0, kd=0, kf=0, time_constant=0.1):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.kf = kf
        self.error_sum = 0
        self.d_term_prev = 0
        self.time_constant = time_constant

    def _calculate(self, reference_value, measured_value, sleep_time):
        error = reference_value - measured_value
        alpha = sleep_time / (self.time_constant + sleep_time)

        self.prev_errors[self.newest_error] = error

        # Proportional term
        p_term = self.kp * error

        # Integral term
        self.error_sum += error
        i_term = self.ki * self.error_sum

        # Derivative term with low pass filter
        raw_d_term = (error - self.prev_errors[self.newest_error_index]) / sleep_time
        d_term = self.d_term_prev + alpha * (raw_d_term - self.d_term_prev)

        # Feedforward term
        ff_term = self.kf * reference_value

        # Calculate the control signal
        control_signal = p_term + i_term + d_term + ff_term

        return control_signal

    def control_loop(
        self,
        get_reference_value,
        get_measured_value,
        set_control_signal,
        sleep_time=0.01,
    ):
        try:
            while True:
                measured_value = get_measured_value()
                reference_value = get_reference_value()
                control_signal = self._calculate(reference_value, measured_value)
                print(f"Control signal: {control_signal}")
                set_control_signal(control_signal)
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            pass
