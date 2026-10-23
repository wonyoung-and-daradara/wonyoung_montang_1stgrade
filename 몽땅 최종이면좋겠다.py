import serial
import time
import matplotlib.pyplot as plt

arduino = serial.Serial('COM6', 115200, timeout=1)

time.sleep(2)
arduino.reset_input_buffer()


def sense():
    #AI 버퍼 버그 수정
    # 빈 줄이나 잘못된 데이터는 계산에 넣지 않음
    try:
        data = arduino.readline().decode('ascii').strip()

        if data:
            return int(data)

    except (ValueError, UnicodeDecodeError):
        return None

    return None

#------------human----------------↓
def inclination_calculate():
    global value_list
    global inclination_5_list

    inclination = value_list[-1] - value_list[-2]
    inclination_5 = (inclination ** 5) / (10 ** 11)

    inclination_5_list.append(inclination_5)
    inclination_5_list = inclination_5_list[-500:]

    return inclination_5

def isgeneral(inclination_5):
    global general

    if inclination_5 >= -10:
        general = True

    # print(general)

    return general

def ispeak(general, inclination_5):
    if inclination_5 < -10 and general == True:
        peak_time_list.append(time_list[-2])
        general = False

        #AI peak 점찍기
        peak_candidate_index_list.append(total_samples - 2)
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

        interval_list[:] = interval_list[-200:]
        bpm_list[:] = bpm_list[-7:]

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

    return bpm_avg


def HRV_calculate():
    global IBI_list

    if len(interval_list) < 2:
        return

    recent = interval_list[-200:]

    #AI 버퍼 버그 수정
    IBI_list = []

    for i in range(1, len(recent)):
        IBI_list.append((recent[i] - recent[i - 1]) ** 2)

    HRV = ((sum(IBI_list) / len(IBI_list)) ** 0.5) * 10001
    print(f"HRV: {HRV}")

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
time_list = []
general = True
#------------human----------------↑


#AI 버퍼 버그 수정
# 제목 갱신에 사용할 계산 결과
bpm_avg = 0
HRV = None

# AI peak 점
total_samples = len(value_list)
x_value = list(range(len(value_list)))

line_1, = ax1.plot(range(len(value_list)), value_list)
line_2, = ax2.plot(
    range(len(inclination_5_list)),
    inclination_5_list
)

# AI peak검출된 곳 표시 코드
peak_flags = [False] * len(value_list)
peak_marker, = ax1.plot([], [], 'ro', markersize=2)

#------------human----------------↓
while (time.time() - first_time) < 10:
    value = sense()

    #AI 버퍼 버그 수정
    if value is None:
        continue

    value_list.append(value)
    value_list = value_list[-500:]

    time_list.append(time.time())
    time_list = time_list[-10:]
#------------human----------------↑

#AI peak 점찍기
# 예열 후 파형과 피크 표시 목록의 길이를 일치시킴
total_samples = len(value_list)
peak_flags = [False] * len(value_list)

#AI 버퍼 버그 수정
last_buffer_check = time.perf_counter()
last_plot_update = time.perf_counter()
plot_interval = 0.05

while True:
    value = sense()

    #AI 버퍼 버그 수정
    if value is None:
        continue

    now = time.perf_counter()

    if now - last_buffer_check >= 1:
        print(f"수신 대기: {arduino.in_waiting} 바이트")
        last_buffer_check = now

    #human
    value_list.append(value)
    time_list.append(time.time())

    value_list = value_list[-500:]
    time_list = time_list[-10:]
    #human end

    total_samples += 1

    #AI peak 점찍기
    # 파형과 피크 표시를 함께 추가하고 같은 길이로 자름
    peak_flags.append(False)
    peak_flags = peak_flags[-500:]

    peak_time_list = peak_time_list[-10:]

    #AI peak 점찍기
    # 직전 샘플이 있어야 기울기와 피크를 계산할 수 있음
    if len(value_list) < 2:
        continue

    inclination_5 = inclination_calculate()
    general = isgeneral(inclination_5)
    general = ispeak(general, inclination_5)

    #AI peak 점찍기
    # 직전 샘플에 해당하는 피크 후보를 처리
    if (
        peak_candidate_index_list
        and peak_candidate_index_list[-1] == total_samples - 2
    ):

        bpm_calculate(peak_candidate_index_list[-1])

        #human
        bpm_avg = bpm_average()
        HRV = HRV_calculate()


        peak_candidate_index_list = peak_candidate_index_list[-1:]

    #AI 버퍼 버그 수정
    # 수신과 계산은 매번 실행하고 그래프만 최대 초당 20번 갱신
    if time.perf_counter() - last_plot_update >= plot_interval:

        # 첫 번째 그래프
        line_1.set_xdata(range(len(value_list)))
        line_1.set_ydata(value_list)

        # 두 번째 그래프
        line_2.set_xdata(range(len(inclination_5_list)))
        line_2.set_ydata(inclination_5_list)

        #AI peak 점찍기
        # 현재 파형과 동일한 인덱스의 위치에 점을 표시
        peak_x = [
            i for i, flag in enumerate(peak_flags) if flag
        ]
        peak_y = [value_list[i] for i in peak_x]

        peak_marker.set_data(peak_x, peak_y)

        #AI 버퍼 버그 수정
        # 축 범위와 제목도 그래프 갱신 시에만 변경
        ax1.set_ylim(value - 5000, value + 5000)
        ax2.set_ylim(inclination_5 - 1000, inclination_5 + 1000)

        plt.title(f"BPM: {bpm_avg:.1f}")
        plt.pause(0.001)

        #AI 버퍼 버그 수정
        # 그리기가 끝난 시각부터 다음 갱신 간격을 계산
        last_plot_update = time.perf_counter()