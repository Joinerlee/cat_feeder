from gpiozero import DigitalInputDevice, DigitalOutputDevice
from time import sleep

class LoadCell:
    """HX711 로드셀 제어를 위한 클래스"""

    def __init__(self, dout_pin=15, sck_pin=14, auto_tare=True, tare_delay=1):
        """
        로드셀 초기화 및 (옵션) 전원 켠 후 자동 영점 보정 수행
        Args:
            dout_pin (int): DOUT 핀 번호 (기본값: 15)
            sck_pin (int): SCK 핀 번호 (기본값: 14)
            auto_tare (bool): 전원 켠 후 자동으로 영점 보정할지 여부 (기본값: True)
            tare_delay (float): 전원 켠 후 영점 보정 전 대기 시간(초) (기본값: 1)
        """
        self.dout = DigitalInputDevice(dout_pin)
        self.sck = DigitalOutputDevice(sck_pin)
        self.OFFSET = 0
        self.SCALE = 1
        self.is_calibrated = False

        if auto_tare:
            print(f"전원 켜짐 후 {tare_delay}초 대기 중...")
            sleep(tare_delay)
            if self.tare():
                print("자동 영점 보정이 완료되었습니다.")
            else:
                print("자동 영점 보정에 실패했습니다.")

    def read_raw_data(self):
        """원시 데이터 읽기"""
        self.sck.off()
        while self.dout.value:
            sleep(0.001)

        data = 0
        for _ in range(24):
            self.sck.on()
            data = (data << 1) | self.dout.value
            self.sck.off()

        # 마지막 펄스 추가 (게인 설정)
        self.sck.on()
        self.sck.off()
        return data

    def tare(self, times=15):
        """
        영점 조정 (여러번 측정 후 평균값을 OFFSET으로 설정)
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

    def get_value(self, times=3):
        """
        보정된 값 읽기 (OFFSET 적용)
        Args:
            times (int): 평균 측정 횟수 (기본값: 3)
        Returns:
            float: 보정된 측정값
        """
        total = 0
        for _ in range(times):
            total += self.read_raw_data() - self.OFFSET
        return float(total / times)

    def get_weight(self, times=3, unit='g'):
        """
        무게 측정
        Args:
            times (int): 평균 측정 횟수 (기본값: 3)
            unit (str): 무게 단위 ('g' 또는 'kg') (기본값: 'g')
        Returns:
            float: 측정된 무게
        """
        if not self.is_calibrated:
            print("경고: 보정이 되지 않은 상태입니다. calibrate()를 먼저 실행하세요.")
        
        value = self.get_value(times)
        weight = value / self.SCALE
        
        if unit == 'kg':
            weight = weight / 1000
            
        return round(weight, 3)

    def calibrate(self, known_weight_g):
        """
        저울 보정
        Args:
            known_weight_g (float): 기준 무게(g)
        Returns:
            bool: 보정 성공 여부
        """
        try:
            print("보정을 시작합니다...")
            print("1. 저울에서 모든 물체를 제거하세요")
            input("준비되면 Enter를 누르세요...")

            self.tare()
            print("영점 조정 완료")

            print(f"\n2. {known_weight_g}g 기준 무게를 올려주세요")
            input("준비되면 Enter를 누르세요...")

            measured_value = self.get_value()
            self.SCALE = measured_value / known_weight_g
            self.is_calibrated = True

            print("보정이 완료되었습니다!")
            return True

        except Exception as e:
            print(f"보정 중 오류 발생: {e}")
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
    # 로드셀 객체 생성 (전원 켠 후 자동 영점 보정 수행)
    loadcell = LoadCell(dout_pin=15, sck_pin=14, auto_tare=True, tare_delay=1)
    
    # 보정 수행 (100g 분동 사용 예시)
    # 주의: 보정 시 자동 영점 보정 값이 초기 OFFSET에 반영되었으므로, 이후 보정을 진행할 수 있습니다.
    loadcell.calibrate(known_weight_g=100)
    
    # 연속 측정 시작
    loadcell.start_measurement()
