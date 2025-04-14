package com.example.server.constant;


public enum TaskStatus {
    IN_QUEUE("IN_QUEUE"),
    IN_PROGRESS("IN_PROGRESS"),
    COMPLETED("COMPLETED"),
    FAILED("FAILED"),
    UNKNOWN("UNKNOWN");

    private final String status;

    TaskStatus(String status) {
        this.status = status;
    }

    @Override
    public String toString() {
        return status;
    }

    /**
     * 根据status获取枚举类，未识别的status返回UNKONWN
     * @param status 字符串
     * @return status对应的枚举类 TaskStatus
     */
    public static TaskStatus fromString(String status) {
        if (status != null) {
            for (TaskStatus s : TaskStatus.values()) {
                if (s.toString().equals(status)) {
                    return s;
                }
            }
        }
        return UNKNOWN;
    }
}