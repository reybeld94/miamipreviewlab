# DEPLOY — Miami Preview Lab

## Bajar cambios del repo

```bash
cd /opt/miamipreviewlab
git pull
systemctl restart mpl-api
journalctl -u mpl-api -n 20 --no-pager
```

## Rollback de código

```bash
cd /opt/miamipreviewlab
git log --oneline       # identificar el commit al que volver
git reset --hard <commit-hash>
systemctl restart mpl-api
```

## Restaurar backup de DB

```bash
# 1. Parar la API
systemctl stop mpl-api

# 2. Ver backups disponibles
ls -lht /opt/miamipreviewlab/data/backups/

# 3. Restaurar el backup elegido
gunzip -k /opt/miamipreviewlab/data/backups/mpl-YYYY-MM-DD_HH-MM.db.gz
cp /opt/miamipreviewlab/data/mpl.db /opt/miamipreviewlab/data/mpl.db.before-restore
mv /opt/miamipreviewlab/data/backups/mpl-YYYY-MM-DD_HH-MM.db /opt/miamipreviewlab/data/mpl.db

# 4. Arrancar la API
systemctl start mpl-api
systemctl status mpl-api --no-pager
```

## Backup manual inmediato

```bash
/opt/miamipreviewlab/scripts/backup_db.sh
```

## Cron schedule

- Backup DB: diario a las 03:30 UTC (`crontab -l` para verificar)
- Rotación: se mantienen los últimos 14 backups
