# 1차 native 검수

궁극기6종의 native 시전·공격 입력, 후방카메라6종전환·직업변경복귀, 각직업방벽/균열과jump입력시나리오의runner/assertion은통과했다. PNG는원본모션·소품담당에게전달했다.

보이는결과: 망치/방패/칼이BetterModel손에나타나며원본cast자세가변화한다. 속성posteffect와HUD아이콘이전환된다. Nova는추가입력없이시전/투사체/폭발후종료한다. 다만Nova의기존enderpearl표시는R2에서자체energyprimitive로교체한다.

결함/추가요구: Titan/Daybreak idle은cast/throwframe을붙잡은snapshot이라다리가고정된다. 사용자지적에따라진짜idle/이동source를다시조사하고locomotion분리를진행한다. 방벽은glassplane,균열은particle뿐이었으므로전용모델을추가한다.

증거제한: melee6종은동시sneak+attack한tick입력을보냈으나서버cooldown이0이었다. 성공으로세지않는다. 클라이언트action과Inputpacket순서차이를피하도록R2에서sneak준비2tick후attack하며서버cooldown을확인한다. rawrunner의nativeMelee=true는입력시퀀스전송만의미하고능력수락증거가아니다.

음원은서버inlinepacket발송로그만확인했다. 청취/숫자원본역할확정은하지않았다. ownedserver/client종료0과최종lease/native중립을확인했다.
