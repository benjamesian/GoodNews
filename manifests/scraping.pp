# Set up the scraping service on a server

service {'scraping.timer':
  ensure    => running,
  enable    => true,
  provider  => systemd,
  require   => File['scraping.timer'],
  subscribe => Exec['daemon-reload'],
}

service {'scraping.service':
  ensure   => stopped,
  enable   => false,
  provider => systemd,
}

file {
  'default':
    ensure => file,
    mode   => '0644',
    owner  => 'root',
    group  => 'root',
    notify => Exec['daemon-reload'];

  'scraping.timer':
    path    => '/etc/systemd/system/scraping.timer',
    source  => '/data/current/GoodNews/etc/systemd/system/scraping.timer',
    require => Exec['stop timer'];

  'scraping.service':
    path    => '/etc/systemd/system/scraping.service',
    source  => '/data/current/GoodNews/etc/systemd/system/scraping.service',
    require => Service['scraping.service'],
    before  => Service['scraping.timer'];
}

exec {'stop timer':
  command     => 'systemctl stop scraping.timer',
  path        => '/usr/bin:/bin',
  refreshonly => false,
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
