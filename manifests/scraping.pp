# Configure the scraping service

service {'scraping.service':
  ensure    => stopped,
  enable    => false,
  require   => File['scraping.service'],
  subscribe => Exec['daemon-reload'],
}

service {'scraping.timer':
  ensure    => running,
  enable    => true,
  require   => [File['scraping.timer'], Service['scraping.service']],
  subscribe => Exec['daemon-reload'],
}

file {'scraping.service':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/scraping.service',
  source => '/data/current/etc/systemd/system/scraping.service',
  notify => Exec['daemon-reload'],
}

file {'scraping.timer':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/scraping.timer',
  source => '/data/current/etc/systemd/system/scraping.timer',
  notify => Exec['daemon-reload'],
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
