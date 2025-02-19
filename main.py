import time
import threading
from queue import Queue
import json
from pathlib import Path
from datetime import datetime
import os

# root 권한 체크
if os.geteuid() != 0:
    print("이 프로그램은 root 권한이 필요합니다.")
    print("'sudo python3 main.py'로 실행해주세요.")
    exit(1)

# GPIO 라이브러리 임포트
try:
    import RPi.GPIO as GPIO
except RuntimeError as e:
    print("Error importing RPi.GPIO! 이 프로그램은 root 권한이 필요합니다!")
    exit(1)

class WeightSensor:
    def __init__(self):
        try:
            # GPIO 설정
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 핀 설정
            self.DOUT = 14
            self.SCK = 15
            
            # GPIO 초기화
            GPIO.setup(self.DOUT, GPIO.IN)
            GPIO.setup(self.SCK, GPIO.OUT)
            GPIO.output(self.SCK, False)
            time.sleep(0.1)  # 센서 안정화 대기
            
            print("무게 센서 GPIO 초기화 완료")
            
            # 데이터 저장을 위한 큐
            self.weight_queue = Queue()
            self.last_weight = 0
            self.weight_change_threshold = 5  # 5g 이상 변화시 감지
            
            # 데이터 저장 경로
            self.data_dir = Path("data")
            self.data_dir.mkdir(exist_ok=True)
            
        except Exception as e:
            print(f"센서 초기화 실패: {str(e)}")
            raise
    
    def read_raw_value(self):
        """HX711 센서 값 읽기"""
        try:
            # DOUT이 LOW가 될 때까지 대기
            while GPIO.input(self.DOUT) == 1:
                pass
            
            data = 0
            for _ in range(24):
                GPIO.output(self.SCK, True)
                time.sleep(0.000001)  # 1μs 딜레이
                GPIO.output(self.SCK, False)
                time.sleep(0.000001)  # 1μs 딜레이
                
                # 비트 읽기
                data = (data << 1) | GPIO.input(self.DOUT)
            
            # 25번째 펄스
            GPIO.output(self.SCK, True)
            time.sleep(0.000001)
            GPIO.output(self.SCK, False)
            time.sleep(0.000001)
            
            # 2의 보수 처리
            if data & 0x800000:
                data |= ~0xffffff
            
            return data
            
        except Exception as e:
            print(f"Raw 값 읽기 실패: {str(e)}")
            return None

    def get_weight(self):
        """무게 값 반환 (그램 단위)"""
        try:
            # 여러 번 측정하여 평균값 사용
            values = []
            for _ in range(3):
                raw = self.read_raw_value()
                if raw is not None:
                    values.append(raw)
                time.sleep(0.1)
            
            if not values:
                return None
            
            average = sum(values) / len(values)
            # 보정 계수 (실제 센서에 맞게 조정 필요)
            weight = (average - 8388608) / 1000
            return round(weight, 1)
            
        except Exception as e:
            print(f"무게 변환 실패: {str(e)}")
            return None

    def monitor_weight(self):
        """무게 변화 모니터링"""
        try:
            print("무게 모니터링 시작...")
            while True:
                current_weight = self.get_weight()
                if current_weight is not None:
                    if abs(current_weight - self.last_weight) > self.weight_change_threshold:
                        print(f"무게 변화 감지: {current_weight}g (변화량: {current_weight - self.last_weight}g)")
                        self.weight_queue.put({
                            'timestamp': datetime.now().isoformat(),
                            'weight': current_weight,
                            'change': current_weight - self.last_weight
                        })
                        self.last_weight = current_weight
                        self.save_weight_data(current_weight)
                
                time.sleep(0.1)
                
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