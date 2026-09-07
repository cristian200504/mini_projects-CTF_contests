#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/fs/fs.h>
#include <zephyr/fs/littlefs.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/flash_map.h>
LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG);

static int littlefs_flash_erase(unsigned int id)
{
	const struct flash_area *pfa;
	int rc;

	rc = flash_area_open(id, &pfa);
	if (rc < 0) {
		LOG_ERR("FAIL: unable to find flash area %u: %d\n",
			id, rc);
		return rc;
	}

	LOG_PRINTK("Area %u at 0x%x on %s for %u bytes\n",
		   id, (unsigned int)pfa->fa_off, pfa->fa_dev->name,
		   (unsigned int)pfa->fa_size);

	/* Optional wipe flash contents */
	if (IS_ENABLED(CONFIG_APP_WIPE_STORAGE)) {
		rc = flash_area_flatten(pfa, 0, pfa->fa_size);
		LOG_ERR("Erasing flash area ... %d", rc);
	}

	flash_area_close(pfa);
	return rc;
}
#define PARTITION_NODE DT_NODELABEL(lfs1)

FS_FSTAB_DECLARE_ENTRY(PARTITION_NODE);

struct fs_mount_t *mountpoint = &FS_FSTAB_ENTRY(PARTITION_NODE);

static int littlefs_mount(struct fs_mount_t *mp)
{
	int rc;

	rc = littlefs_flash_erase((uintptr_t)mp->storage_dev);
	if (rc < 0) {
		return rc;
	}

	/* Do not mount if auto-mount has been enabled */
	LOG_PRINTK("%s automounted\n", mp->mnt_point);
	
	return 0;
}

int main()
{
    int rc = littlefs_mount(mountpoint);
    if (rc < 0)
    {
        LOG_ERR("Failed to mount littlefs: %d", rc);
        return rc;
    }

	LOG_INF("Trying to load flag from memory...");

	struct fs_file_t file;
	fs_file_t_init(&file);

	rc = fs_open(&file, "/lfs1/flag.txt", FS_O_READ);
	if (rc < 0)
	{
		LOG_ERR("Failed to open flag: %d.", rc);
		return rc;
	}

	char buf[100];
	rc = fs_read(&file, buf, sizeof(buf));
	if (rc < 0)
	{
		LOG_ERR("Failed to read flag: %d", rc);
		return rc;
	}
	buf[rc] = 0;

	LOG_INF("Flag is: %s", buf);

	fs_close(&file);
}
