package com.heartguard.portal.model.api;

public record DeviceDto(
    String id,
    String serial,
    String brand,
    String model,
    String deviceTypeCode,
    String deviceTypeLabel,
    String ownerPatientId,
    String ownerPatientName,
    Boolean active
) {
}
