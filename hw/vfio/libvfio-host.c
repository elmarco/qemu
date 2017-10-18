/*
 * libvfio library
 *
 * Copyright (c) 2017 Red Hat, Inc.
 *
 * Authors:
 *  Marc-André Lureau <mlureau@redhat.com>
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or
 * later.  See the COPYING file in the top-level directory.
 */
#include "libvfio-priv.h"
#include <sys/ioctl.h>

static bool
libvfio_host_init_container(libvfio *vfio, libvfio_container *container,
                            Error **errp)
{
    int ret, fd = qemu_open("/dev/vfio/vfio", O_RDWR);

    if (fd < 0) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "failed to open /dev/vfio/vfio");
        return false;
    }

    ret = ioctl(fd, VFIO_GET_API_VERSION);
    if (ret != VFIO_API_VERSION) {
        error_setg(errp, ERR_PREFIX "supported vfio version: %d, "
                   "reported version: %d", VFIO_API_VERSION, ret);
        qemu_close(fd);
        return false;
    }

    container->vfio = vfio;
    container->fd = fd;
    return true;
}

static void
libvfio_host_container_deinit(libvfio_container *container)
{
    if (container->fd >= 0) {
        qemu_close(container->fd);
        container->fd = -1;
    }
}

static bool
libvfio_host_container_check_extension(libvfio_container *container,
                                       int ext, Error **errp)
{
    int ret = ioctl(container->fd, VFIO_CHECK_EXTENSION, ext);

    if (ret < 0) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "ioctl(CHECK_EXTENSION) failed");
        return false;
    } else if (ret > 0) {
        return true;
    }
    return false;
}

static bool
libvfio_host_container_set_iommu(libvfio_container *container, int iommu_type,
                                 Error **errp)
{
    if (ioctl(container->fd, VFIO_SET_IOMMU, iommu_type)) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "failed to set iommu for container");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_get_info(libvfio_container *container,
                                      struct vfio_iommu_type1_info *info,
                                      Error **errp)
{
    info->argsz = sizeof(*info);
    if (ioctl(container->fd, VFIO_IOMMU_GET_INFO, info)) {
        error_setg_errno(errp, errno, ERR_PREFIX "failed to get iommu info");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_enable(libvfio_container *container, Error **errp)
{
    if (ioctl(container->fd, VFIO_IOMMU_ENABLE)) {
        error_setg_errno(errp, errno, ERR_PREFIX "failed to enable container");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_map_dma(libvfio_container *container,
                                     uint64_t vaddr, uint64_t iova,
                                     uint64_t size, uint32_t flags,
                                     Error **errp)
{
    struct vfio_iommu_type1_dma_map map = {
        .argsz = sizeof(map),
        .flags = flags,
        .vaddr = vaddr,
        .iova = iova,
        .size = size,
    };

    /*
     * Try the mapping, if it fails with EBUSY, unmap the region and try
     * again.  This shouldn't be necessary, but we sometimes see it in
     * the VGA ROM space.
     */
    if (ioctl(container->fd, VFIO_IOMMU_MAP_DMA, &map) == 0) {
        return true;
    }

    if (errno != EBUSY) {
        goto error;
    }

    if (!libvfio_container_iommu_unmap_dma(container, iova, size, 0, NULL)) {
        goto error;
    }

    if (ioctl(container->fd, VFIO_IOMMU_MAP_DMA, &map) == 0) {
        return true;
    }

error:
    error_setg_errno(errp, errno, ERR_PREFIX "IOMMU_MAP_DMA failed");
    return false;
}

static bool
libvfio_host_container_iommu_unmap_dma(libvfio_container *container,
                                       uint64_t iova, uint64_t size,
                                       uint32_t flags, Error **errp)
{
    struct vfio_iommu_type1_dma_unmap unmap = {
        .argsz = sizeof(unmap),
        .flags = 0,
        .iova = iova,
        .size = size,
    };

    if (ioctl(container->fd, VFIO_IOMMU_UNMAP_DMA, &unmap)) {
        error_setg_errno(errp, errno, ERR_PREFIX "IOMMU_UNMAP_DMA failed");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_spapr_tce_get_info(libvfio_container *container,
                                                struct vfio_iommu_spapr_tce_info *info,
                                                Error **errp)
{
    info->argsz = sizeof(*info);
    if (ioctl(container->fd, VFIO_IOMMU_SPAPR_TCE_GET_INFO, info)) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "IOMMU_SPAPR_TCE_GET_INFO failed");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_spapr_register_memory(libvfio_container *container,
                                                   uint64_t vaddr,
                                                   uint64_t size,
                                                   uint32_t flags,
                                                   Error **errp)
{
    struct vfio_iommu_spapr_register_memory reg = {
        .argsz = sizeof(reg),
        .vaddr = vaddr,
        .size = size,
        .flags = flags,
    };

    if (ioctl(container->fd, VFIO_IOMMU_SPAPR_REGISTER_MEMORY, &reg)) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "IOMMU_SPAPR_REGISTER_MEMORY failed");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_spapr_unregister_memory(libvfio_container *container,
                                                     uint64_t vaddr,
                                                     uint64_t size,
                                                     uint32_t flags,
                                                     Error **errp)
{
    struct vfio_iommu_spapr_register_memory reg = {
        .argsz = sizeof(reg),
        .vaddr = vaddr,
        .size = size,
        .flags = flags,
    };

    if (ioctl(container->fd, VFIO_IOMMU_SPAPR_UNREGISTER_MEMORY, &reg)) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "IOMMU_SPAPR_UNREGISTER_MEMORY failed");
        return false;
    }

    return true;
}

static bool
libvfio_host_container_iommu_spapr_tce_create(libvfio_container *container,
                                              uint32_t page_shift,
                                              uint64_t window_size,
                                              uint32_t levels,
                                              uint32_t flags,
                                              uint64_t *start_addr,
                                              Error **errp)
{
    struct vfio_iommu_spapr_tce_create create = {
        .argsz = sizeof(create),
        .page_shift = page_shift,
        .window_size = window_size,
        .levels = levels,
        .flags = flags
    };

    if (!ioctl(container->fd, VFIO_IOMMU_SPAPR_TCE_CREATE, &create)) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "IOMMU_SPAPR_TCE_CREATE failed");
        return false;
    }

    *start_addr = create.start_addr;
    return true;
}

static bool
libvfio_host_container_iommu_spapr_tce_remove(libvfio_container *container,
                                              uint64_t start_addr,
                                              Error **errp)
{
    struct vfio_iommu_spapr_tce_remove remove = {
        .argsz = sizeof(remove),
        .start_addr = start_addr,
    };

    if (ioctl(container->fd, VFIO_IOMMU_SPAPR_TCE_REMOVE, &remove)) {
        error_setg(errp, ERR_PREFIX "Failed to remove window at %"PRIx64,
                   (uint64_t)remove.start_addr);
        return false;
    }

    return true;
}

static bool
libvfio_host_container_eeh_pe_op(libvfio_container *container,
                                 uint32_t op, Error **errp)
{
    struct vfio_eeh_pe_op pe_op = {
        .argsz = sizeof(pe_op),
        .op = op,
    };

    if (ioctl(container->fd, VFIO_EEH_PE_OP, &pe_op)) {
        error_setg_errno(errp, errno,
                         ERR_PREFIX "EEH_PE_OP 0x%x failed", op);
        return false;
    }

    return true;
}

static libvfio_ops libvfio_host_ops = {
    .init_container = libvfio_host_init_container,
    .container_deinit = libvfio_host_container_deinit,
    .container_check_extension = libvfio_host_container_check_extension,
    .container_set_iommu = libvfio_host_container_set_iommu,
    .container_iommu_get_info = libvfio_host_container_iommu_get_info,
    .container_iommu_enable = libvfio_host_container_iommu_enable,
    .container_iommu_map_dma = libvfio_host_container_iommu_map_dma,
    .container_iommu_unmap_dma = libvfio_host_container_iommu_unmap_dma,
    .container_iommu_spapr_tce_get_info = libvfio_host_container_iommu_spapr_tce_get_info,
    .container_iommu_spapr_register_memory = libvfio_host_container_iommu_spapr_register_memory,
    .container_iommu_spapr_unregister_memory = libvfio_host_container_iommu_spapr_unregister_memory,
    .container_iommu_spapr_tce_create = libvfio_host_container_iommu_spapr_tce_create,
    .container_iommu_spapr_tce_remove = libvfio_host_container_iommu_spapr_tce_remove,
    .container_eeh_pe_op = libvfio_host_container_eeh_pe_op,
};

bool
libvfio_init_host(libvfio *vfio, int api_version, Error **errp)
{
    assert(vfio);

    if (VFIO_API_VERSION != api_version) {
        error_setg(errp, ERR_PREFIX "supported vfio version: %d, "
                   "client version: %d", VFIO_API_VERSION, api_version);
        return false;
    }

    vfio->fd = -1;
    vfio->ops = &libvfio_host_ops;
    return true;
}
