import os
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from time import sleep

class LoadCell:
    """HX711 로드셀 제어를 위한 클래스"""

    CALIBRATION_FILE = "calibration.cfg"

    def __init__(self, dout_pin=15, sck_pin=14, auto_tare=True, tare_delay=1):
        """
        로드셀 초기화  
        - 전원 켠 후 자동 영점 보정(tare)  
        - 저장된 보정 파일(calibration.cfg)이 있으면 SCALE 값을 불러옴  
        
        Args:
            dout_pin (int): DOUT 핀 번호 (기본값: 15)
            sck_pin (int): SCK 핀 번호 (기본값: 14)
            auto_tare (bool): 전원 켠 후 자동으로 영점 보정할지 여부 (기본값: True)
            tare_delay (float): 전원 켠 후 영점 보정 전 대기 시간(초) (기본값: 1)
        """
        self.dout = DigitalInputDevice(dout_pin)
        self.sck = DigitalOutputDevice(sck_pin)
        self.OFFSET = 0
        self.SCALE = 1  # 보정되지 않은 상태의 기본 SCALE
        self.is_calibrated = False

        if auto_tare:
            print(f"전원 켠 후 {tare_delay}초 대기 중...")
            sleep(tare_delay)
            if self.tare():
                print("자동 영점 보정(Zero Tare)이 완료되었습니다.")
            else:
                print("자동 영점 보정에 실패했습니다.")

        # 이전 보정값이 있으면 자동으로 불러옴
        if os.path.exists(self.CALIBRATION_FILE):
            if self.load_calibration(self.CALIBRATION_FILE):
                print("보정 파일에서 SCALE 값을 불러왔습니다.")
            else:
                print("보정 파일 불러오기에 실패했습니다.")
        else:
            print("보정 파일이 없습니다. 최초 보정을 진행해주세요.")

    def read_raw_data(self):
        """원시 데이터 읽기"""
        self.sck.off()
        # DOUT 신호가 준비될 때까지 대기
        while self.dout.value:
            sleep(0.001)

        data = 0
        for _ in range(24):
            self.sck.on()
            data = (data << 1) | self.dout.value
            self.sck.off()

        # 마지막 펄스로 게인 설정
        self.sck.on()
        self.sck.off()
        return data

    def tare(self, times=15):
        """
        영점 조정 (여러 번 측정 후 평균값을 OFFSET으로 설정)
        
        Args:
            times (int): 평균 측정 횟수 (기본값: 15)
        
        Returns:
            bool: 영점 조정 성공 여부
        """
        try:
            total = 0
            for _ in range(times):
                total += self.read_raw_data()
            self.OFFSET = total / times
            return True
        except Exception as e:
            print(f"영점 조정 중 오류 발생: {e}")
            return False

    def get_value(self, times=7):
        """
        보정된 값 읽기 (OFFSET 적용 및 이상치 제거)
        
        Args:
            times (int): 측정 횟수 (기본값: 7)
        
        Returns:
            float: 보정된 측정값
        """
        readings = []
        for _ in range(times):
            readings.append(self.read_raw_data() - self.OFFSET)
            sleep(0.005)  # 짧은 딜레이 추가

        # 충분한 측정값이 있으면 최대, 최소값을 제거하여 이상치를 보정
        if len(readings) >= 5:
            readings.sort()
            filtered = readings[1:-1]
        else:
            filtered = readings

        return float(sum(filtered) / len(filtered))

    def get_weight(self, times=7, unit='g'):
        """
        무게 측정
        
        Args:
            times (int): 측정 횟수 (기본값: 7)
            unit (str): 무게 단위 ('g' 또는 'kg') (기본값: 'g')
        
        Returns:
            float: 측정된 무게
        """
        if not self.is_calibrated:
            print("경고: 보정이 되지 않은 상태입니다. 올바른 무게를 얻으려면 calibrate()를 실행하거나 저장된 보정값 파일을 사용하세요.")
        
        value = self.get_value(times)
        weight = value / self.SCALE
        
        if unit == 'kg':
            weight = weight / 1000
            
        return round(weight, 3)

    def calibrate(self, known_weight_g):
        """
        저울 보정 (예: 100g 기준 보정)  
        최초 보정 시 100g 분동을 올려놓고 진행하면, SCALE 값이 계산되어 저장됩니다.
        
        Args:
            known_weight_g (float): 기준 무게(g) (예: 100)
        
        Returns:
            bool: 보정 성공 여부
        """
        try:
            print("########################################")
            print("보정 안내:")
            print("1. 저울 위의 모든 물체를 제거해주세요.")
            print("2. 준비되면 Enter를 눌러 영점 보정을 진행합니다.")
            print("########################################")
            input("Enter를 누르세요...")

            if self.tare():
                print("영점 보정(Zero Tare)이 완료되었습니다.")
            else:
                print("영점 보정에 실패했습니다. 다시 시도해주세요.")
                return False

            print("########################################")
            print(f"보정을 위해 {known_weight_g}g 기준 분동을 저울 위에 올려주세요.")
            print("준비되면 Enter를 눌러 진행합니다.")
            print("########################################")
            input("Enter를 누르세요...")

            measured_value = self.get_value(times=15)
            self.SCALE = measured_value / known_weight_g
            self.is_calibrated = True

            print("보정이 완료되었습니다!")
            print(f"측정된 기준값: {measured_value:.3f}")
            print(f"계산된 SCALE 값: {self.SCALE:.6f}")

            # 보정값을 파일에 저장
            self.save_calibration(self.CALIBRATION_FILE)
            print("보정값이 파일에 저장되었습니다.")
            return True

        except Exception as e:
            print(f"보정 중 오류 발생: {e}")
            return False

    def save_calibration(self, filename):
        """
        현재 보정값(OFFSET과 SCALE)을 파일에 저장
        
        Args:
            filename (str): 저장할 파일 이름
        """
        try:
            with open(filename, "w") as f:
                # OFFSET은 보정 시에 계속 사용하지만, SCALE이 핵심임
                f.write(f"{self.OFFSET}\n")
                f.write(f"{self.SCALE}\n")
        except Exception as e:
            print(f"보정값 저장 실패: {e}")

    def load_calibration(self, filename):
        """
        파일에서 보정값(OFFSET과 SCALE)을 불러옴
        
        Args:
            filename (str): 불러올 파일 이름
        
        Returns:
            bool: 보정값 불러오기 성공 여부
        """
        try:
            with open(filename, "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    self.OFFSET = float(lines[0].strip())
                    self.SCALE = float(lines[1].strip())
                    self.is_calibrated = True
                    return True
                else:
                    return False
        except Exception as e:
            print(f"보정값 불러오기 실패: {e}")
            return False

    def start_measurement(self, interval=0.5):
        """
        연속 측정 시작
        
        Args:
            interval (float): 측정 간격(초) (기본값: 0.5)
        """
        try:
            print("측정을 시작합니다. (종료: Ctrl+C)")
            while True:
                weight = self.get_weight()
                print(f"현재 무게: {weight}g")
                sleep(interval)
        except KeyboardInterrupt:
            print("\n측정을 종료합니다.")

# 사용 예시
if __name__ == "__main__":
    # 로드셀 객체 생성 (자동 영점 보정 수행 및 저장된 보정값 사용 시 자동 로드)
    loadcell = LoadCell(dout_pin=15, sck_pin=14, auto_tare=True, tare_delay=1)
    
    # 만약 최초 보정이 필요하다면 아래 주석을 해제하고 100g 분동으로 보정 진행
    # loadcell.calibrate(known_weight_g=100)
    
    # 연속 측정 시작
    loadcell.start_measurement()
