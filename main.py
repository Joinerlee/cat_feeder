import time
import threading
from queue import Queue
import json
from pathlib import Path
import RPi.GPIO as GPIO
from datetime import datetime

class WeightSensor:
    def __init__(self):
        # GPIO 설정
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 핀 설정
        self.DOUT = 14
        self.SCK = 15
        
        # GPIO 초기화
        GPIO.setup(self.DOUT, GPIO.IN)
        GPIO.setup(self.SCK, GPIO.OUT)
        print("무게 센서 GPIO 초기화 완료")
        
        # 데이터 저장을 위한 큐
        self.weight_queue = Queue()
        self.last_weight = 0
        self.weight_change_threshold = 5  # 5g 이상 변화시 감지
        
        # 데이터 저장 경로
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def read_raw_value(self):
        """실제 HX711 센서 값 읽기"""
        while GPIO.input(self.DOUT):
            time.sleep(0.0001)
        
        data = 0
        for _ in range(24):
            GPIO.output(self.SCK, True)
            time.sleep(0.0001)
            GPIO.output(self.SCK, False)
            time.sleep(0.0001)
            data = (data << 1) | GPIO.input(self.DOUT)
        
        GPIO.output(self.SCK, True)
        time.sleep(0.0001)
        GPIO.output(self.SCK, False)
        
        if data & 0x800000:
            data |= ~0xffffff
        
        return data

    def get_weight(self):
        """무게 값 반환 (그램 단위)"""
        raw_value = self.read_raw_value()
        # 보정 계수 (실제 센서에 맞게 조정 필요)
        weight = (raw_value - 8388608) / 1000
        return round(weight, 1)

    def monitor_weight(self):
        """무게 변화 모니터링"""
        try:
            while True:
                current_weight = self.get_weight()
                
                # 유의미한 무게 변화 감지
                if abs(current_weight - self.last_weight) > self.weight_change_threshold:
                    print(f"무게 변화 감지: {current_weight}g")
                    self.weight_queue.put({
                        'timestamp': datetime.now().isoformat(),
                        'weight': current_weight,
                        'change': current_weight - self.last_weight
                    })
                    self.last_weight = current_weight
                    
                    # 데이터 저장
                    self.save_weight_data(current_weight)
                
                time.sleep(0.1)  # 100ms 간격으로 측정
                
        except KeyboardInterrupt:
            print("\n무게 모니터링 중단")
        except Exception as e:
            print(f"무게 측정 오류: {str(e)}")
        finally:
            self.cleanup()

    def save_weight_data(self, weight):
        """무게 데이터 저장"""
        data_file = self.data_dir / "weight_data.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'weight': weight
        }
        
        # 파일에 데이터 추가
        try:
            if data_file.exists():
                with open(data_file, 'r') as f:
                    existing_data = json.load(f)
                existing_data.append(data)
            else:
                existing_data = [data]
                
            with open(data_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            print(f"데이터 저장 오류: {str(e)}")

    def cleanup(self):
        """GPIO 정리"""
        try:
            GPIO.cleanup()
            print("무게 센서 GPIO 정리 완료")
        except:
            pass

def main():
    sensor = None
    try:
        sensor = WeightSensor()
        print("\n무게 모니터링 시작...")
        print("Ctrl+C를 눌러 종료\n")
        sensor.monitor_weight()
        
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    except Exception as e:
        print(f"예상치 못한 오류: {str(e)}")
    finally:
        if sensor:
            sensor.cleanup()

if __name__ == "__main__":
    main()