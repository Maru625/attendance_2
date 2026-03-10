"""
list_cameras.py
- 시스템에 연결된 모든 카메라 장치를 나열하는 유틸리티
- 각 인덱스별로 이름, 해상도 등을 표시
"""

import cv2
from pygrabber.dshow_graph import FilterGraph


def main():
    print("=" * 50)
    print("  시스템 카메라 목록")
    print("=" * 50)

    # DirectShow를 통해 카메라 이름 조회
    try:
        graph = FilterGraph()
        devices = graph.get_input_devices()
        print(f"\n총 {len(devices)}개의 카메라 장치 발견:\n")
        for i, name in enumerate(devices):
            print(f"  인덱스 {i}: {name}")
    except Exception as e:
        print(f"\n카메라 이름 조회 실패 (pygrabber 에러): {e}")
        print("인덱스만 확인합니다...\n")
        for i in range(7):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"  인덱스 {i}: 사용 가능 ({w}x{h})")
                cap.release()
            else:
                print(f"  인덱스 {i}: 없음")

    print("\n" + "=" * 50)
    print("대상 프로그램에서 'OBS Virtual Camera' 인덱스를 선택하세요.")
    print("=" * 50)


if __name__ == "__main__":
    main()
