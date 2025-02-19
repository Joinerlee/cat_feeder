from gpiozero import DistanceSensor
from time import sleep

# 거리 센서 핀 설정 (예: 트리거: 23, 에코: 24)
sensor = DistanceSensor(echo=23, trigger=24)

def get_scaled_proximity(sensor, threshold=1.0, max_distance=3.0):
    """
    sensor: gpiozero의 DistanceSensor 객체
    threshold: 임계 거리 (m) - 이 거리 이내면 1.0 반환 (예, 1m 이하)
    max_distance: 최대 거리 (m) - 이 거리 이상이면 0.0 반환 (예, 3m 이상)
    
    threshold와 max_distance 사이에서는 선형 보간하여 1.0에서 0.0까지 값을 반환합니다.
    """
    distance = sensor.distance  # 단위: m
    
    if distance <= threshold:
        return 1.0
    elif distance >= max_distance:
        return 0.0
    else:
        # threshold (1m)와 max_distance (3m) 사이에서 선형 보간
        # distance가 threshold일 때 1.0, max_distance일 때 0.0이 되어야 하므로:
        scaled = 1 - (distance - threshold) / (max_distance - threshold)
        return scaled

if __name__ == "__main__":
    THRESHOLD = 1.0      # 1m 이내이면 최대값(1.0)
    MAX_DISTANCE = 3.0   # 3m 이상이면 최소값(0.0)
    
    while True:
        proximity = get_scaled_proximity(sensor, threshold=THRESHOLD, max_distance=MAX_DISTANCE)
        print(f"Raw distance: {sensor.distance:.2f} m, Proximity value: {proximity:.2f}")
        sleep(1)
