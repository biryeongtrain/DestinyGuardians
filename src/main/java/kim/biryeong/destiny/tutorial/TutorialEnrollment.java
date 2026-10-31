package kim.biryeong.destiny.tutorial;

/** Persist a rollout revision, so legacy completion does not exempt existing accounts. */
final class TutorialEnrollment {
    static final int REQUIRED_REVISION = 1;
    private TutorialEnrollment() {}
    static boolean required(int completedRevision, boolean active) {
        return completedRevision < REQUIRED_REVISION && !active;
    }
}
