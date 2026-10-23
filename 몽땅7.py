import serial
import time
import matplotlib.pyplot as plt

arduino = serial.Serial('COM6', 115200, timeout=1)

time.sleep(2)
arduino.reset_input_buffer()


def sense():
    data = arduino.readline().decode('ascii').strip()

    if data:
        return int(data)

    return None


def inclination_calculate():
    global value_list
    global inclination_5_list
    inclination = value_list[-1] - value_list[-2]
    inclination_5 = (inclination ** 5) / (10 ** 11)
    inclination_5_list.append(inclination_5)
    inclination_5_list = inclination_5_list[-500:]
    # print(inclination_5_list)
    return inclination_5


def isgeneral(inclination_5):
    global general
    if inclination_5 >= -1:
        general = True
    print(general)
    return general

def ispeak(general, inclination_5):
    if inclination_5 < -1 and general == True:
        peak_time_list.append(time.time())
        general = False
        # AI peak 계산
        peak_candidate_index_list.append(total_samples - 1)
        return general
    else:
        return general

def bpm_calculate(peak_index):
    global peak_time_list
    if len(peak_time_list) < 2:
        #AI peak 점찍기
        visible_index = peak_index - (total_samples - len(peak_flags))
        if 0 <= visible_index < len(peak_flags):
            peak_flags[visible_index] = True
        return
    interval = peak_time_list[-1] - peak_time_list[-2]
    if interval <= 0.3:
        peak_time_list.pop(-1)
        return
    else:
        interval_list.append(interval)
        bpm = 60 / interval
        bpm_list.append(bpm)
        #print(f"&&&&&&&&&&&&&&{bpm}&&&&&&&&&&&&&")
        print(f"피크 간격: {interval:.3f}초, BPM: {bpm:.1f}")

        #AI peak 점찍기
        visible_index = peak_index - (total_samples - len(peak_flags))

        if 0 <= visible_index < len(peak_flags):
            peak_flags[visible_index] = True
        return


def bpm_average():
    global bpm_list
    if len(bpm_list) < 7:
        return 0
    recent_bpm = bpm_list[-7:]
    bpm_avg = sum(recent_bpm) / len(recent_bpm)
    print(recent_bpm)
    return bpm_avg


def HRV_calculate():
    if len(interval_list) < 2:
        return
    recent = interval_list[-200:]

    for i in range(1, len(recent)):
        IBI_list.append((interval_list[-i] - interval_list[- (i + 1)]) ** 2)
    HRV = ((sum(IBI_list) / len(IBI_list)) ** 0.5) * 1000
    return HRV


# AI peak 점
peak_candidate_index_list = []

value_list = []
first_time = time.time()
inclination_5_list = [0, 0]

plt.ion()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 5))
ax1.set_xlim(0, 500)
ax2.set_xlim(0, 500)

peak_time_list = []
bpm = 0
interval_list = []
IBI_list = []
peak_candidate_list = []
bpm_list = []
uptrend = False

while (time.time() - first_time) < 10:
    value = sense()
    value_list.append(value)
    value_list = value_list[-500:]

general = True

# AI peak 점
total_samples = len(value_list)

x_value = list(range(len(value_list)))

line_1, = ax1.plot(range(len(value_list)), value_list)
line_2, = ax2.plot(range(len(inclination_5_list)), inclination_5_list)

# AI peak검출된 곳 표시 코드
peak_flags = [False] * len(value_list)
peak_marker, = ax1.plot([], [], 'ro', markersize=2)

while True:
    value = sense()
    value_list.append(value)
    value_list = value_list[-500:]

    total_samples += 1

    # AI peak검출된 곳 표시 코드
    peak_flags.append(False)
    peak_flags = peak_flags[-500:]
    peak_time_list = peak_time_list[-10:]

    inclination_5 = inclination_calculate()
    general = isgeneral(inclination_5)
    general = ispeak(general, inclination_5)

    #AI peak 점찍기
    if peak_candidate_index_list and peak_candidate_index_list[-1] == total_samples - 1:
        bpm_calculate(peak_candidate_index_list[-1])

    bpm_avg = bpm_average()
    HRV = HRV_calculate()

    # AI
    # 첫 번째 그래프
    line_1.set_xdata(range(len(value_list)))
    line_1.set_ydata(value_list)

    # 두 번째 그래프
    line_2.set_xdata(range(len(inclination_5_list)))
    line_2.set_ydata(inclination_5_list)

    # AI peak검출된 곳 표시 코드
    peak_x = [i for i, flag in enumerate(peak_flags) if flag]
    peak_y = [value_list[i] for i in peak_x]

    peak_marker.set_data(peak_x, peak_y)

    # human
    ax1.set_ylim(value - 5000, value + 5000)
    ax2.set_ylim(inclination_5 - 1000, inclination_5 + 1000)
    # print(uptrend)
    # print(peak_candidate_list[-5:])
    print(f"HRV: {HRV}")
    plt.title(f"BPM: {bpm_avg:.1f}")
    plt.pause(0.001)